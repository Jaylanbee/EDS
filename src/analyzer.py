import pandas as pd
import sqlite3
import os

class EDSAnalyzer:
    def __init__(self, data_path: str = None):
        """
        Initialize the analyzer.
        EDS is now a Phase 2 Dynamic Read-Only Consumer of the RDQ SQLite database.
        """
        # We will use the SQLite DB instead of CSV
        self.db_path = os.getenv('ECOSYSTEM_DB_PATH', os.path.expanduser('~/.education_ecosystem/review_index.db'))

    def _fetch_dynamic_roi_data(self) -> pd.DataFrame:
        """
        Fetches the ROI weights dynamically from the SQLite DB.
        """
        if not os.path.exists(self.db_path):
            print(f"Warning: Database not found at {self.db_path}")
            return pd.DataFrame()

        try:
            conn = sqlite3.connect(self.db_path)

            # Using the schema provided for Phase 2 dynamic query
            query = """
            SELECT
                w.item_id AS eds_x_code,
                w.subject,
                w.weakness_score,
                e.exam_weight,
                w.weakness_score * COALESCE(e.exam_weight, 0.1) AS selection_score
            FROM weakness_stats w
            LEFT JOIN exam_weights e ON w.item_id = e.item_id
            """

            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching dynamic data: {e}")
            return pd.DataFrame()

    def module_b_trap_analysis(self) -> pd.DataFrame:
        """
        In the new dynamic architecture, we mock trap analysis based on selection score.
        """
        df = self._fetch_dynamic_roi_data()
        if df.empty:
            return pd.DataFrame()

        # Assuming higher selection score means it's a priority/trap
        trap_questions = df.sort_values('selection_score', ascending=False).copy()

        # Mocking loss_reason
        trap_questions['失分原因'] = '概念錯誤/推理不足'
        trap_questions['X軸主代碼'] = trap_questions['eds_x_code']
        trap_questions['avg_difficulty'] = trap_questions['exam_weight'] # fallback map
        return trap_questions

    def module_d_priority_score(self, mode: str = "A++", personal_modifiers: dict = None) -> pd.DataFrame:
        """
        D-1 Priority Score & D-3 ROI & D-4 ROI Ranking.
        This now acts as a dynamic Read-Only consumer of the SQLite DB.
        """
        df = self._fetch_dynamic_roi_data()
        if df.empty:
            return pd.DataFrame()

        merged = df.copy()
        merged['X軸主代碼'] = merged['eds_x_code']

        # The base priority is the selection score from the DB
        # Scale to 100 for readability
        merged['Base_Priority'] = merged['selection_score'] * 100

        # Apply Adaptive Engine modifiers if provided (though Phase 2 DB might already handle some weakness)
        if personal_modifiers:
            def apply_modifier(row):
                code = row['X軸主代碼']
                mod = personal_modifiers.get(code, 1.0)
                return row['Base_Priority'] * mod

            merged['Priority_Score'] = merged.apply(apply_modifier, axis=1)
        else:
            merged['Priority_Score'] = merged['Base_Priority']

        # D-3 Calculate Expected Score Gain (ROI = Priority / Estimated Hours)
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
