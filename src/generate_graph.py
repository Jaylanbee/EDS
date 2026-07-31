import os
import pandas as pd
from src.analyzer import EDSAnalyzer
from src.adaptive_engine import AdaptiveEngine

def generate_decision_graph_text(data_path: str = None, available_hours: float = 2.0, target_mode: str = 'A++') -> str:
    """Generates the text-based Application Layer Output (決勝圖譜) and returns it as a string."""
    analyzer = EDSAnalyzer()

    adaptive_engine = AdaptiveEngine()
    modifiers = adaptive_engine.get_priority_modifiers()
    latest_weakness = adaptive_engine.get_latest_weakness_summary()

    roi_df = analyzer.module_d_priority_score(mode=target_mode, personal_modifiers=modifiers)
    trap_df = analyzer.module_b_trap_analysis()

    if roi_df.empty:
        return "Failed to calculate ROI."

    selected_topics = []
    accumulated_hours = 0.0

    for _, row in roi_df.iterrows():
        est_time = row.get('預估補強時間', 2.0)
        if pd.isna(est_time): est_time = 2.0

        if accumulated_hours < available_hours:
            selected_topics.append(row)
            accumulated_hours += est_time
        else:
            break

    output_lines = []

    if latest_weakness:
        rdq_topic = latest_weakness.get('topic')
        rdq_reason = latest_weakness.get('reason', '觀念不夠熟練')
        output_lines.append(f"收到 RDQ 傳來的資料！我看到你在『{rdq_topic}』的「{rdq_reason}」上還有點卡關。")
        output_lines.append(f"距離實戰越來越近，我們今天先不念課本，直接來看歷屆會考最常考的題型，準備好了嗎？\n")

    output_lines.append(f"📅 今天（{available_hours} 小時）該讀：\n")

    for i, topic in enumerate(selected_topics):
        topic_code = topic['X軸主代碼']
        stars = topic['評等']
        output_lines.append(f"{(i+1):02d} {topic_code}    效益 {stars}")

    output_lines.append(f"\n⏱ 預估投入：{accumulated_hours:.1f} 小時")

    score_gain_est = min(len(selected_topics) * 1.5, 5.0)
    output_lines.append(f"📈 預估提升：{score_gain_est:.1f} 分")

    main_weakness = "無明顯弱點資料"
    if not trap_df.empty:
         common_reasons = trap_df['失分原因'].value_counts()
         if not common_reasons.empty:
             main_weakness = common_reasons.index[0]

    output_lines.append(f"🎯 主要改善方向：{main_weakness}")

    trap_warning = "請留意常見題型陷阱。"
    if not trap_df.empty:
        worst_trap = trap_df.iloc[0]
        trap_warning = f"複習 {worst_trap['X軸主代碼']} 時，留意「{worst_trap['失分原因']}」相關陷阱。"

    output_lines.append(f"⚠️ 常見陷阱：{trap_warning}")

    return "\n".join(output_lines)

def generate_decision_graph(data_path: str = None, output_path: str = "outputs/daily_suggestion.txt", available_hours: float = 2.0, target_mode: str = 'A++'):
    """Legacy wrapper for terminal execution."""
    print(f"Initializing Phase 2 dynamic EDS Analyzer")
    output_text = generate_decision_graph_text(None, available_hours, target_mode)

    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)

    print(f"\n=== 決勝圖譜 (Decision Graph) ===")
    print(output_text)
    print(f"=================================")
    print(f"\nOutput saved to {output_path}")

if __name__ == "__main__":
    # Ensure outputs directory exists
    os.makedirs('outputs', exist_ok=True)
    generate_decision_graph(None, 'outputs/daily_suggestion.txt')
