import pandas as pd

class EDSAnalyzer:
    def __init__(self, data_path: str):
        """Initialize the analyzer with the tagging dataset."""
        try:
            self.df = pd.read_csv(data_path)
            # Ensure proper types
            self.df['年份'] = pd.to_numeric(self.df['年份'], errors='coerce')
            self.df['通過率'] = pd.to_numeric(self.df['通過率'], errors='coerce')
            self.df['預估補強時間_小時'] = pd.to_numeric(self.df['預估補強時間_小時'], errors='coerce')
        except FileNotFoundError:
            print(f"Error: Dataset {data_path} not found.")
            self.df = pd.DataFrame()

    def module_a_high_frequency(self) -> pd.DataFrame:
        """A-1 高頻分析 (High-frequency analysis)"""
        if self.df.empty: return pd.DataFrame()

        # Group by 'X軸主代碼' (treating it as 次主題 for now as per methodology)
        grouped = self.df.groupby('X軸主代碼').agg(
            出現次數=('通過率', 'size'),
            平均通過率=('通過率', 'mean')
        ).reset_index().sort_values('出現次數', ascending=False)

        grouped['累積題數'] = grouped['出現次數'].cumsum()
        grouped['累積覆蓋率'] = grouped['累積題數'] / grouped['出現次數'].sum()

        # Classify based on coverage
        def classify_coverage(cov):
            if cov <= 0.7:
                return '核心'
            elif cov <= 0.9:
                return '延伸'
            else:
                return '低頻'

        grouped['分類'] = grouped['累積覆蓋率'].apply(classify_coverage)
        return grouped

    def module_a_stability(self) -> pd.DataFrame:
        """A-2 命題穩定度分析 (Stability Score)"""
        if self.df.empty or '年份' not in self.df.columns: return pd.DataFrame()

        # Create a crosstab of Year and X-axis main code
        stability = self.df.groupby(['X軸主代碼', '年份']).size().unstack(fill_value=0)
        stability_binary = (stability > 0).astype(int)

        # Calculate appearance rate (assuming 5 years for methodology example)
        appearance_rate = stability_binary.mean(axis=1)

        # Recent weights (adjust according to available years)
        # Assuming years are like 111, 112, 113, 114, 115 for the methodology example.
        # We will dynamically assign weights to the top 5 most recent years available in the data
        available_years = sorted([y for y in stability_binary.columns if pd.notna(y)])

        weights = {}
        if len(available_years) > 0:
            # Simple increasing weight strategy for up to 5 recent years
            base_weights = [0.1, 0.15, 0.2, 0.25, 0.3]
            # Match weights from the most recent backwards
            recent_years = available_years[-5:]
            for i, y in enumerate(recent_years):
                # Ensure weight index aligns with how many recent years we actually have
                weight_idx = len(base_weights) - len(recent_years) + i
                weights[y] = base_weights[weight_idx]

        stability_score = stability_binary.apply(
            lambda row: sum(row[y] * w for y, w in weights.items() if y in stability_binary.columns),
            axis=1
        )

        result = pd.DataFrame({
            'X軸主代碼': appearance_rate.index,
            '出現率': appearance_rate.values,
            '穩定度分數': stability_score.values
        })

        # Basic logic for interpretation (can be refined)
        def interpret_stability(row):
            if row['出現率'] >= 0.8 and row['穩定度分數'] >= 0.2:
                 return '核心穩定'
            elif row['穩定度分數'] >= 0.2 and row['出現率'] < 0.6:
                 return '近期竄升'
            else:
                 return '偶發'

        result['判讀'] = result.apply(interpret_stability, axis=1)
        return result

    def module_b_trap_analysis(self) -> pd.DataFrame:
        """B-1 陷阱題分析 (Trap Question Analysis)"""
        if self.df.empty or '通過率' not in self.df.columns: return pd.DataFrame()

        mean_p = self.df['通過率'].mean()
        sd_p = self.df['通過率'].std()

        # Method 2 (relative threshold) with cap at 40%
        threshold = min(40, mean_p - sd_p)

        trap_questions = self.df[self.df['通過率'] < threshold].copy()
        return trap_questions.sort_values('通過率')

    def module_c_type_stats(self) -> pd.DataFrame:
         """C-3 題型攻略 (資料驅動部分)"""
         if self.df.empty or '題型' not in self.df.columns: return pd.DataFrame()

         type_stats = self.df.groupby('題型').agg(
             題數=('通過率', 'size'),
             平均通過率=('通過率', 'mean')
         ).sort_values('平均通過率').reset_index()

         # Assign priority based on rank (lower pass rate = higher priority)
         type_stats['優先度'] = range(1, len(type_stats) + 1)
         return type_stats

    def _normalize(self, s: pd.Series) -> pd.Series:
        if s.max() == s.min():
            return pd.Series(0.5, index=s.index)
        return (s - s.min()) / (s.max() - s.min())

    def module_d_priority_score(self, mode: str = 'A++') -> pd.DataFrame:
        """D-1 Priority Score & D-3 ROI & D-4 ROI Ranking"""
        if self.df.empty: return pd.DataFrame()

        # Get A-1 and A-2 results
        freq_df = self.module_a_high_frequency()
        stab_df = self.module_a_stability()

        if freq_df.empty: return pd.DataFrame()

        # Calculate integration complexity (average number of secondary codes)
        def count_subcodes(val):
            if pd.isna(val) or str(val).strip() == '': return 0
            return len(str(val).split(','))

        self.df['次代碼數量'] = self.df['X軸次代碼'].apply(count_subcodes)

        complexity_df = self.df.groupby('X軸主代碼').agg(
            次代碼平均數=('次代碼數量', 'mean'),
            預估補強時間=('預估補強時間_小時', 'mean')
        ).reset_index()

        # Get mode mode (most frequent) recoverability per main code
        def mode_val(x):
            return x.mode().iloc[0] if not x.mode().empty else None

        recover_df = self.df.groupby('X軸主代碼').agg(
            可救程度=('可救程度', mode_val)
        ).reset_index()

        # Merge them all
        merged = freq_df.merge(stab_df[['X軸主代碼', '穩定度分數']], on='X軸主代碼', how='left')
        merged = merged.merge(complexity_df, on='X軸主代碼', how='left')
        merged = merged.merge(recover_df, on='X軸主代碼', how='left')

        # Fill NA stability with 0
        merged['穩定度分數'] = merged['穩定度分數'].fillna(0)
        merged['次代碼平均數'] = merged['次代碼平均數'].fillna(0)

        # Calculate Priority Score based on weights
        weights_map = {
            '保A': (0.60, 0.20, 0.10, 0.10),
            'A+': (0.45, 0.30, 0.15, 0.10),
            'A++': (0.35, 0.35, 0.20, 0.10),
        }
        w1, w2, w3, w4 = weights_map.get(mode, weights_map['A++'])

        merged['Priority_Score'] = (
            w1 * self._normalize(merged['出現次數']) +
            w2 * self._normalize(100 - merged['平均通過率']) +
            w3 * self._normalize(merged['穩定度分數']) +
            w4 * self._normalize(merged['次代碼平均數'])
        ) * 100 # Scale to 100 for readability

        # D-3 Calculate Expected Score Gain (ROI = Priority / Estimated Hours)
        # Avoid division by zero
        safe_hours = merged['預估補強時間'].apply(lambda x: max(0.5, x) if pd.notna(x) else 2.0)
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

        return merged
