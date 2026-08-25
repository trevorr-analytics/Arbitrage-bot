import re

file_path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\sports_model\dashboard.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We will use textwrap.dedent to clean up the indentation of the html blocks
import textwrap

new_content = content.replace(
    '''        html += f"""
        <div style="font-size:0.85em; color:#a0a0a0; padding: 5px 0px 0px 15px; border-left: 2px solid #333; margin-top:5px;">
            <b>MC Sim:</b> W: {sim['win_prob']*100:.1f}% | D: {sim['draw_prob']*100:.1f}% | L: {sim['loss_prob']*100:.1f}% <br>
            <b>Most Likely Scores:</b> {scores_str} <br>
            <b>Totals:</b> O1.5: {sim['ov15']*100:.1f}% | O2.5: {sim['ov25']*100:.1f}% | BTTS: {sim['btts_yes']*100:.1f}%
        </div>
        """''',
    '''        import textwrap
        mc_html = f"""
<div style="font-size:0.85em; color:#a0a0a0; padding: 5px 0px 0px 15px; border-left: 2px solid #333; margin-top:5px;">
    <b>MC Sim:</b> W: {{sim['win_prob']*100:.1f}}% | D: {{sim['draw_prob']*100:.1f}}% | L: {{sim['loss_prob']*100:.1f}}% <br>
    <b>Most Likely Scores:</b> {{scores_str}} <br>
    <b>Totals:</b> O1.5: {{sim['ov15']*100:.1f}}% | O2.5: {{sim['ov25']*100:.1f}}% | BTTS: {{sim['btts_yes']*100:.1f}}%
</div>
"""
        html += textwrap.dedent(mc_html)'''
)

# Wait, regex is safer for replacing to avoid exact indentation mismatch.
import re

content = re.sub(
    r'html \+= f"""\n\s*<div style="font-size:0\.85em.*?</div>\n\s*"""',
    lambda m: m.group(0).replace('            ', '').replace('        ', ''),
    content,
    flags=re.DOTALL
)

# And also for the initial leg-row HTML
content = re.sub(
    r'html = f"""\n\s*<div class="leg-row">\n\s*<b>.*?</i>\n\s*"""',
    lambda m: m.group(0).replace('    ', ''),
    content,
    flags=re.DOTALL
)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
