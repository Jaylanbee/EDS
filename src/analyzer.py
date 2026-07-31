import pandas as pd

class EDSAnalyzer:
    def __init__(self, data_path: str):
        """
        Initialize the analyzer.
        EDS is now a Read-Only Consumer of the RDQ-maintained eds_roi_weights.csv.
        """
        try:
            self.df = pd.read_csv(data_path)
        except FileNotFoundError:
            print(f"Error: Dataset {data_path} not found.")
            self.df = pd.DataFrame()

    def module_b_trap_analysis(self) -> pd.DataFrame:
        """
        Legacy trap analysis.
        In the new Read-Only architecture, we just identify items with high difficulty.
        """
        if self.df.empty or 'avg_difficulty' not in self.df.columns:
            return pd.DataFrame()

        # Assuming higher avg_difficulty means it's a trap/harder.
        trap_questions = self.df.sort_values('avg_difficulty', ascending=False).copy()

        # Mocking loss_reason as the new summary CSV doesn't provide it directly per question
        trap_questions['失分原因'] = '概念錯誤/推理不足'
        trap_questions['X軸主代碼'] = trap_questions['eds_x_code']
        return trap_questions

    def module_d_priority_score(self, mode: str = "A++", personal_modifiers: dict = None) -> pd.DataFrame:
        """
        D-1 Priority Score & D-3 ROI & D-4 ROI Ranking.
        This now acts as a Read-Only consumer of eds_roi_weights.csv calculated by RDQ.
        """
        if self.df.empty or 'roi_weight' not in self.df.columns:
            return pd.DataFrame()

        merged = self.df.copy()
        merged['X軸主代碼'] = merged['eds_x_code']

        # Base Priority is primarily derived from the upstream ROI weight
        # Scale to 100 for readability
        merged['Base_Priority'] = merged['roi_weight'] * 100

        # Apply Adaptive Engine modifiers if provided
        if personal_modifiers:
            def apply_modifier(row):
                code = row['X軸主代碼']
                mod = personal_modifiers.get(code, 1.0)
                return row['Base_Priority'] * mod

            merged['Priority_Score'] = merged.apply(apply_modifier, axis=1)
        else:
            merged['Priority_Score'] = merged['Base_Priority']

        # D-3 Calculate Expected Score Gain (ROI = Priority / Estimated Hours)
        # Using a flat estimated hours for now since upstream summary doesn't provide it yet
        safe_hours = 2.0
        merged['效益_ROI'] = merged['Priority_Score'] / safe_hours

        # Sort by ROI descending
        merged = merged.sort_values('效益_ROI', ascending=False).reset_index(drop=True)

        # D-4 Assign Stars (Top 20% = 5 stars, etc.)
        def assign_stars(rank, total):
            pct = rank / total if total > 0 else 0
            if pct <= 0.2: return '★★★★★'
            elif pct <= 0.4: return '★★★★☆'
            elif pct <= 0.6: return '★★★☆☆'
            elif pct <= 0.8: return '★★☆☆☆'
            else: return '★☆☆☆☆'

        merged['評等'] = merged.index.to_series().apply(lambda idx: assign_stars(idx, len(merged)))

        # Map back fields required by the UI
        merged['預估補強時間'] = safe_hours

        return merged
