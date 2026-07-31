import os
import pandas as pd
from src.analyzer import EDSAnalyzer
from src.adaptive_engine import AdaptiveEngine

def generate_decision_graph_text(data_path: str = None, available_hours: float = 2.0, target_mode: str = 'A++', target_subject: str = None) -> str:
    """Generates the text-based Application Layer Output (決勝圖譜) and returns it as a string."""
    analyzer = EDSAnalyzer()

    adaptive_engine = AdaptiveEngine()
    modifiers = adaptive_engine.get_priority_modifiers()
    latest_weakness = adaptive_engine.get_latest_weakness_summary()

    roi_df = analyzer.module_d_priority_score(mode=target_mode, personal_modifiers=modifiers, target_subject=target_subject)
    trap_df = analyzer.module_b_trap_analysis(target_subject=target_subject)

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
        output_lines.append(f"已為你對接 RDQ 的檢傷紀錄！發現你在『{rdq_topic}』的『概念理解』上有發揮空間。")
        output_lines.append(f"考前黃金時間，我們直接進入 **50%~70% 難度甜頭區** 的會考真題特訓，用出題來鍛造你的記憶。準備好開始挑戰了嗎？\n")

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

def generate_decision_graph(data_path: str = None, output_path: str = "outputs/daily_suggestion.txt", available_hours: float = 2.0, target_mode: str = 'A++', target_subject: str = None):
    """Legacy wrapper for terminal execution."""
    print(f"Initializing Phase 2 dynamic EDS Analyzer")
    output_text = generate_decision_graph_text(None, available_hours, target_mode, target_subject)

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
