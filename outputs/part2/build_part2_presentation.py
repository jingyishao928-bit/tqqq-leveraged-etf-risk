"""Rebuild the Part 2 slides using the original group's PowerPoint master."""
import argparse
from copy import deepcopy
import csv
from datetime import date
import json
from math import log2
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_MARKER_STYLE
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.packuri import PackURI
from pptx.util import Inches, Pt

PART2_ROOT = Path(__file__).resolve().parent

PAPER = 'FFFFFF'
WHITE = 'FFFFFF'
INK = '34383C'
MUTED = '62676B'
FAINT = 'D0D3D5'
SOFT = 'F2F3F4'
RED = 'A53746'
RED_LIGHT = 'F0D8DC'
NAVY = '344D64'
GREEN = '346852'
GREEN_LIGHT = 'DCE8E1'
SLATE = '667786'
FONT = 'Times New Roman'
SANS = FONT
BODY = set()
FRAME = []


def fit_y(s, y):
    return 2.78 + (y-1.80)*.772 if s.part in BODY else y


def color(hex_value):
    return RGBColor.from_string(hex_value)


def tx(s, value, x, y, w, h, size=16, tone=INK, *, bold=False,
       italic=False, font=FONT, align=PP_ALIGN.LEFT, url=None, name=None):
    box = s.shapes.add_textbox(Inches(x), Inches(fit_y(s,y)), Inches(w), Inches(h*.86 if s.part in BODY else h))
    box.name = name or value.replace('\n', ' ')[:85]
    tf = box.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for index, part in enumerate(value.split('\n')):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_before = p.space_after = Pt(0)
        p.line_spacing = 1.01
        run = p.add_run()
        run.text = part
        if url:
            run.hyperlink.address = url
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color(tone)
    return box


def line(s, x1, y1, x2, y2, tone=FAINT, width=.7, dashed=False):
    shape = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(fit_y(s,y1)), Inches(x2), Inches(fit_y(s,y2)))
    shape.line.color.rgb = color(tone)
    shape.line.width = Pt(width)
    if dashed:
        shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return shape


def block(s, x, y, w, h, fill, round_=False):
    geometry = MSO_SHAPE.OVAL if round_ else MSO_SHAPE.RECTANGLE
    shape = s.shapes.add_shape(geometry, Inches(x), Inches(fit_y(s,y)), Inches(w), Inches(h*.772 if s.part in BODY else h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color(fill)
    shape.line.fill.background()
    return shape


def dot(s, x, y, fill, diameter=.095):
    return block(s, x-diameter/2, y-diameter/2, diameter, diameter, fill, True)


def path(s, xy, tone, width=1.6, dashed=False, name=None):
    first, *rest = [(Inches(x), Inches(fit_y(s,y))) for x, y in xy]
    form = s.shapes.build_freeform(*first)
    form.add_line_segments(rest, close=False)
    shape = form.convert_to_shape()
    if name:
        shape.name = name
    shape.fill.background()
    shape.line.color.rgb = color(tone)
    shape.line.width = Pt(width)
    if dashed:
        shape.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return shape


def background(s, fill=PAPER):
    s._element.set('showMasterSp', '0')
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = color(fill)


def update_text(shape, content):
    frame = shape.text_frame
    first = frame.paragraphs[0]
    for paragraph in frame.paragraphs[1:]:
        element = paragraph._element
        element.getparent().remove(element)
    runs = first.runs
    runs[0].text = content
    for extra in runs[1:]:
        element = extra._r
        element.getparent().remove(element)


def foot(s, label, n):
    BODY.discard(s.part)
    update_text(s.shapes[2], f'{int(n)+6:02d}' if n.isdigit() else n)
    update_text(s.shapes[8], label)


def head(s, title, sub, *, size=28.5):
    for element in FRAME:
        s.shapes._spTree.insert_element_before(deepcopy(element), 'p:extLst')
    update_text(s.shapes[5],title)
    s.shapes[5].text_frame.paragraphs[0].runs[0].font.size = Pt(size)
    update_text(s.shapes[6],sub)
    BODY.add(s.part)


def new(p, layout, fill=PAPER):
    s = p.slides.add_slide(layout)
    for shape in list(s.placeholders):
        element = shape._element
        element.getparent().remove(element)
    background(s, fill)
    return s


def note(s, body):
    s.notes_slide.notes_text_frame.text = body


def pp(n, signed=False):
    return (f'{100*n:+.2f}' if signed else f'{100*n:.2f}').replace('-', '−')


def typ(s):
    return s.replace('-', '−')


def book_table(s, headers, rows, x, y, widths, row_h=.52, size=16, accents=None):
    x_positions = [x + sum(widths[:i]) for i in range(len(widths))]
    for row_number, row in enumerate([headers, *rows]):
        y_start = y + row_number*row_h
        for column, value in enumerate(row):
            numeric = column > 0
            text_tone = MUTED if row_number == 0 else INK
            if accents:
                text_tone = accents.get((row_number-1,column),text_tone)
            tx(s,value,x_positions[column]+.06,y_start+.025,widths[column]-.12,row_h-.06,
               11.2 if row_number==0 else size,text_tone,bold=(row_number==0 or column==0 or text_tone in (RED,GREEN)),
               font=SANS if row_number==0 else FONT,align=PP_ALIGN.RIGHT if numeric else PP_ALIGN.LEFT)
        line(s,x,y_start+row_h,x+sum(widths),y_start+row_h,SLATE if row_number==0 else FAINT,.78 if row_number==0 else .55)


def group(data, days, band, label):
    return next(g for g in data['groups'] if g['window_days']==days
                and g['band']==band and g['direction']=='Near flat' and g['vol_group']==label)


def cover(s):
    update_text(s.shapes[6], 'How daily resets turn benchmark moves into position risk.')
    update_text(s.shapes[8], 'LEVERAGED ETF RISK ANALYSIS')
    note(s, 'About 9 seconds. I will explain how TQQQ’s daily leverage target turns the benchmark path into different holding-period returns and tail losses.')


def round_trip(s):
    update_text(s.shapes[5], 'A flat round trip cost the 3× path 5.45%')
    update_text(s.shapes[6], 'Hypothetical example · QQQ rises 10.00% and falls 9.09% · starting wealth $1.00')
    chart = s.shapes[7].chart
    data = CategoryChartData()
    data.categories = ['Start','Day 1','Day 2']
    ideal_end = 1.30*(1-3/11)
    data.add_series('QQQ benchmark', [1,1.10,1])
    data.add_series('Ideal daily 3×', [1,1.30,ideal_end])
    chart.replace_data(data)
    for series,tone in zip(chart.series, ('4B8B70','C64752')):
        series.smooth = False
        series.format.line.color.rgb = color(tone)
        series.format.line.width = Pt(2.25)
        series.marker.style = XL_MARKER_STYLE.CIRCLE
        series.marker.size = 6
        series.marker.format.fill.solid()
        series.marker.format.fill.fore_color.rgb = color(tone)
        series.marker.format.line.fill.background()
    chart.value_axis.minimum_scale = .9
    chart.value_axis.maximum_scale = 1.35
    chart.value_axis.major_unit = .1
    chart.value_axis.tick_labels.number_format = '$0.00'
    chart.value_axis.tick_labels.number_format_is_linked = False
    for text_style in (chart.value_axis.tick_labels.font,chart.category_axis.tick_labels.font,chart.legend.font):
        text_style.name = FONT
        text_style.size = Pt(11)
    update_text(s.shapes[9], 'DAILY RESET BEFORE COSTS')
    update_text(s.shapes[10], 'W')
    paragraph = s.shapes[10].text_frame.paragraphs[0]
    paragraph.runs[0].font.size = Pt(23)
    style = deepcopy(paragraph.runs[0]._r.get_or_add_rPr())
    for run in paragraph.runs:
        paragraph._p.remove(run._r)
    for text, is_subscript in (('W', False), ('t', True), (' = W', False), ('t-1', True),
                               ('(1 + 3r', False), ('t', True), (')', False)):
        run = paragraph.add_run()
        run.text = text
        formatting = deepcopy(style)
        if is_subscript:
            formatting.set('baseline', '-25000')
        run._r.insert(0, formatting)
    update_text(s.shapes[12], 'FINAL WEALTH PER $1')
    update_text(s.shapes[13], f'QQQ $1.00  ·  Ideal 3× ${ideal_end:.4f}')
    s.shapes[13].text_frame.paragraphs[0].runs[0].font.size = Pt(18)
    update_text(s.shapes[15], 'RMSC 5003 CH. 4–5 · AVELLANEDA & ZHANG (2010) · JARROW (2010)')
    note(s, 'About 44 seconds. Think of a one-day exposure of three times NAV with the excess funded, before costs. The fund then resets exposure to three times the new NAV. Start at one dollar. QQQ rises ten percent and then falls one eleventh, about 9.09 percent, returning to one dollar. The ideal three-times path rises thirty percent, then loses three elevenths of its now larger base. It finishes at about 94.55 cents, a 5.45 percent loss. The slide isolates the mechanics before expenses or tracking differences.')


def wealth_history(s, base, metrics):
    head(s,'TQQQ finished below both 3× comparisons',
         'Daily QQQ-based wealth · 2 Jan 2019 to 20 Nov 2026 · $1.00 at the first close')
    with (base/'tables/part2_cumulative_path.csv').open(newline='') as handle:
        rows = list(csv.DictReader(handle))
    days = [date.fromisoformat(r['date']) for r in rows]
    kinds = [
        ('daily_3x_qqq_wealth','Ideal daily 3×', NAVY, False, '+', 'bench_qqq_ideal_daily_return'),
        ('linear_3x_qqq_wealth','Linear 3×', SLATE, True, '+', 'bench_qqq_linear_return'),
        ('tqqq_wealth','Actual TQQQ', RED, False, '+', 'TQQQ_cumulative_return'),
    ]
    a, b, t, base = 1.24,9.55,2.02,5.92
    w_min, w_max = .75,40
    plot_x = lambda d: a+(b-a)*((d-days[0]).days/(days[-1]-days[0]).days)
    plot_y = lambda w: t+(base-t)*(log2(w_max)-log2(w))/(log2(w_max)-log2(w_min))
    spans = [
        ('2020-02-20','2020-03-23',SOFT), ('2020-03-24','2020-09-02','F4F2EF'),
        ('2022-01-04','2022-12-30',SOFT), ('2025-04-01','2025-04-30',RED_LIGHT),
    ]
    for begin,end,shade in spans:
        x0, x1 = [plot_x(date.fromisoformat(v)) for v in (begin,end)]
        block(s,x0,t,x1-x0,base-t,shade)
    tx(s,'COVID sell-off / rebound',plot_x(date(2020,2,20))-.33,1.80,1.65,.18,10,MUTED,font=SANS)
    tx(s,'2022 rate hikes',plot_x(date(2022,1,4))+.10,1.80,1.19,.18,10,MUTED,font=SANS)
    tx(s,'Apr 2025',plot_x(date(2025,4,1))-.24,1.80,.86,.18,10,MUTED,font=SANS)
    for w in (1,2,4,8,16,32):
        y=plot_y(w)
        line(s,a,y,b,y,SLATE if w==1 else FAINT,.78 if w==1 else .54)
        tx(s,f'${w:g}',.72,y-.117,.38,.23,11,MUTED,font=SANS,align=PP_ALIGN.RIGHT)
    for year in range(2019,2027):
        x=plot_x(max(days[0],date(year,1,1)))
        tx(s,str(year),x-.24,5.97,.48,.25,11,MUTED,font=SANS,align=PP_ALIGN.CENTER)
    final_labels = [2.02,2.78,3.55]
    for (key,label,tone,dashed,prefix,display), label_y in zip(kinds,final_labels):
        xy = [(plot_x(d),plot_y(float(row[key]))) for d,row in zip(days,rows)]
        path(s,xy,tone,1.95 if tone==RED else 1.52,dashed,label)
        ex, ey = xy[-1]
        dot(s,ex,ey,tone,.075)
        path(s,[(ex,ey),(ex+.16,ey),(ex+.34,label_y+.11),(ex+.51,label_y+.11)],tone,.65)
        tx(s,label,10.13,label_y,2.47,.23,13,tone,bold=True,font=SANS)
        tx(s,prefix+metrics[display],10.11,label_y+.26,2.46,.41,24,tone,bold=True)
    tx(s,'Wealth per $1, log scale',.74,6.40,3.30,.25,12,MUTED,font=SANS)
    tx(s,'Endpoint labels show cumulative returns.',8.78,6.40,3.81,.25,12,MUTED,font=SANS,align=PP_ALIGN.RIGHT)
    foot(s,'Part 1 frozen dataset · 1,983 returns · formal NDX comparison in the appendix', '02')
    note(s,'About 62 seconds. The log-scaled chart compares three paths from one dollar. The ideal daily path reinvests three times each QQQ daily return. The linear path applies three times the cumulative QQQ return once. Actual is the adjusted TQQQ wealth. The full-sample outcomes are 1,626.69 percent ideal, 935.65 percent linear and 823.07 percent actual. The ideal reset outperformed the linear multiple over this strongly rising sample. The real fund underperformed both. NDX is the formal benchmark and it gives the same ranking. On the NDX basis the reset effect added 478.49 percentage points versus the linear comparator, while actual was 535.87 points below the ideal. The appendix separates the fee scenario and residual.')


def volatility(s, base, data, metrics):
    head(s,'More volatility deepened the drag in near-flat markets',
         'Ideal daily 3× return minus linear 3× return · QQQ-based, non-overlapping 21-day windows',size=28.5)
    with (base/'tables/part2_research_disjoint_windows.csv').open(newline='') as handle:
        rows = [r for r in csv.DictReader(handle) if r['direction']=='Near flat']
    left,right = 2.48,8.53
    xx = lambda v: left+(right-left)*(v+4.38)/4.45
    for val in (-4,-3,-2,-1,0):
        x=xx(val)
        line(s,x,2.64,x,5.69,SLATE if val==0 else FAINT,.82 if val==0 else .56,val==0)
        tx(s,f'{val:g}'.replace('-','−'),x-.26,5.76,.52,.28,12,MUTED,font=SANS,align=PP_ALIGN.CENTER)
    for vol,label,tone,light,y in (
        ('Lower RMS','Lower volatility',GREEN,GREEN_LIGHT,3.32),
        ('Higher RMS','Higher volatility',RED,RED_LIGHT,4.64),
    ):
        g=group(data, 21,.03,vol)
        tx(s,label,.76,y-.30,1.62,.28,15,tone,bold=True)
        tx(s,f'{g["n"]} windows',.77,y+.02,1.61,.23,12,MUTED,font=SANS)
        for i,r in enumerate(r for r in rows if r['vol_group']==vol):
            x=xx(float(r['reset_gap'])*100)
            dot(s,x,y+[-.15,-.08,0,.08,.15][i%5],light,.09)
        lo, med, hi = [xx(100*g[q]) for q in ('q25','median','q75')]
        line(s,lo,y,hi,y,tone,3)
        dot(s,med,y,tone,.145)
        tx(s,f'{pp(g["median"])} pp',med-.71,y-.62,1.42,.36,22,tone,bold=True,align=PP_ALIGN.CENTER)
    tx(s,'Reset gap (percentage points)',3.47,6.18,4.08,.27,13,MUTED,font=SANS,align=PP_ALIGN.CENTER)
    line(s,8.96,2.57,8.96,6.22,FAINT)
    tx(s,'April 2025',9.32,2.65,3.21,.35,18,INK,bold=True)
    tx(s,typ(metrics['choppy_reset_gap']),9.30,3.05,3.21,.77,45,RED,bold=True)
    tx(s,'Ideal return vs linear',9.33,3.98,3.20,.33,15,MUTED)
    tx(s,f'QQQ  +{metrics["choppy_qqq_return"]}\nIdeal 3×  {typ(metrics["choppy_daily_3x_qqq_return"])}',
       9.33,4.65,3.15,.64,18)
    foot(s,'Near flat means QQQ within ±3%. Lines span the middle 50%. The volatility split is 18.87% annualized RMS, measured ex post.', '03')
    note(s,'About 66 seconds. We begin with 94 non-overlapping blocks, keep the 34 with QQQ between minus 3 and plus 3 percent, and split on the historical median annualized root mean square daily return of 18.87 percent. The bold dots show medians. The higher-volatility group has a median shortfall of 1.24 percentage points, compared with 0.52 for the lower-volatility group. The lines show the middle half of the observations. These are retrospective comparisons for Chapter 5 stress analysis. April 2025 puts the intuition in historical terms. QQQ gained 1.40 percent, but the ideal daily fund lost 3.38 percent, so the reset gap was negative 7.57 points. The 2020 recovery shows that a powerful trend can more than offset the drag in arithmetic returns.')


def losses(s, metrics):
    head(s,'The position determines which tail hurts',
         'Fixed-share positions · positive values denote losses per $1 of initial exposure',size=28.5)
    for x, title, formula, detail, number, tone in (
        (.70,'LONG TQQQ','1 − W','Loss rises as the fund falls.',
         f'Historical drawdown  {typ(metrics["TQQQ_max_drawdown"])}',INK),
        (6.79,'SHORT TQQQ','W − 1','Loss rises as the fund rallies.',
         f'Worst historical short P&L  {typ(metrics["short_tqqq_worst_mark_per_dollar"])} per $1',RED),
    ):
        block(s,x,2.06,5.80,2.82,SOFT)
        tx(s,title,x+.22,2.24,5.30,.29,13,MUTED,bold=True)
        tx(s,formula,x+.21,2.62,5.32,1.04,49,tone)
        tx(s,detail,x+.23,3.86,5.28,.39,19,INK)
        tx(s,number,x+.23,4.38,5.25,.31,14,MUTED)
    tx(s,'Simulate the benchmark path, revalue the fund, then estimate VaR and ES.',
       .72,5.43,11.77,.42,21,INK,bold=True)
    tx(s,'W is TQQQ terminal wealth rebased to $1.00. The historical short P&L excludes borrow costs.',
       .74,6.06,11.72,.30,13,MUTED)
    foot(s,'RMSC 5003 CH. 4: EXPOSURE MAPPING  ·  CH. 7–8: VOLATILITY  ·  CH. 6: VaR AND ES', '04')
    note(s,'About 62 seconds. TQQQ had an 81.66 percent peak-to-trough drawdown, versus 35.12 percent for QQQ. For a fixed-share position the relevant loss uses the rebased wealth. A long loss occurs on the downside. A short loses on the upside and can lose more than its initial notional. Our worst short mark was negative 18.46 dollars of P&L per initial dollar, before borrowing costs. These historical statistics illustrate the asymmetry. Chapter 4 gives the exposure mapping, Chapter 7 gives the conditional paths, Chapter 8 covers diagnostics, and Chapter 6 applies VaR and expected shortfall to the resulting loss distribution. This sets up Part 3 at one, ten and twenty-one days.')


def funding(s, data, metrics):
    head(s,'The NDX log bridge isolates reset drag',
         'A constant disclosed expense rate estimates fee sensitivity · log contributions are additive')
    vals = [r for r in data['bridge'] if r['benchmark']=='NDX']
    starts = [0]+[r['log_level'] for r in vals[:-1]]
    curve = [(start,r['log_level'],r['log_increment']) for start,r in zip(starts,vals)]
    curve.append((0,vals[-1]['log_level'],vals[-1]['log_level']))
    graph_x=lambda i: 1.79+i*1.28
    graph_y=lambda v: 5.60-v*.77
    for i in range(5):
        y=graph_y(i)
        line(s,1.14,y,7.57,y,FAINT,.56)
        tx(s,str(100*i),.73,y-.11,.30,.22,10,MUTED,font=SANS,align=PP_ALIGN.RIGHT)
    for i,(start,end,delta) in enumerate(curve):
        x,y=graph_x(i), graph_y(max(start,end))
        tone = NAVY if i==0 else RED if i==1 else SLATE if i<4 else INK
        block(s,x-.285,y,.57,max(.034,abs(start-end)*.77),tone)
        prefix = '+' if i in (0,4) else ''
        tx(s,prefix+pp(delta),x-.47,y-.33,.94,.26,13,tone,bold=True,align=PP_ALIGN.CENTER)
        if i<4:
            line(s,x+.286,graph_y(end),graph_x(i+1)-.286,graph_y(end),SLATE,.65,True)
    for i,label in enumerate(('3× index\nlog growth','Exact reset\npenalty','Net fee\nscenario','Other\nresidual','Actual\nlog growth')):
        tx(s,label,graph_x(i)-.61,5.73,1.22,.56,12,INK,align=PP_ALIGN.CENTER)
    tx(s,'Log points',.72,6.32,1.1,.22,11,MUTED,font=SANS)
    line(s,7.86,2.14,7.86,6.32,FAINT)
    book_table(s,['NDX fee setting','Annual rate','Terminal wealth'],[
        (label,metrics[f'fee_ndx_{key}_annual_fee'],metrics[f'fee_ndx_{key}_terminal_wealth'])
        for label,key in [('Fee-free','no_fee'),('Net','net'),('Gross','gross')]
    ],8.13,2.19,[1.65,1.23,1.60],.55,15)
    tx(s,'Daily tracking-error SD, annualized',8.18,4.73,4.34,.29,15,INK,bold=True)
    tx(s,f'NDX {metrics["NDX_annual_tracking_error"]}  ·  QQQ {metrics["QQQ_annual_tracking_error"]}',
       8.18,5.10,4.34,.35,20,INK)
    tx(s,'The residual combines financing, trading,\nmarket-price and benchmark effects.',8.18,5.65,4.41,.57,15,MUTED)
    foot(s,'ProShares expense snapshot · Charupat & Miu (2014) · Jarrow (2010) · Tang & Xu (2013)', 'A1')
    note(s,'The log bridge starts with three times the NDX log growth. The first decrement is exact discrete reset drag. The second is the constant net-fee scenario, then the residual to actual. The net-fee input is a disclosed snapshot. Actual historical expenses and other costs cannot be separately measured with these inputs. Arithmetic percentage-point gaps answer a different comparison.')


def stress(s, metrics):
    head(s,'Trend can offset the arithmetic reset drag',
         'Historical stress episodes · each path starts at $1.00 before its first return')
    scenarios = [('COVID sell-off','crash'),('COVID rebound','rebound'),
                 ('2022 rate hikes','bear'),('April 2025 volatility','choppy')]
    rows = [(label, metrics[f'{k}_observations'],typ(metrics[f'{k}_qqq_return']),typ(metrics[f'{k}_tqqq_return']),
             typ(metrics[f'{k}_daily_3x_qqq_return']),typ(metrics[f'{k}_linear_3x_qqq_return']),typ(metrics[f'{k}_reset_gap']))
            for label,k in scenarios]
    book_table(s,['Historical episode','Days','QQQ','Actual TQQQ','Ideal 3×','Linear 3×','Reset gap'],
               rows,.78,2.26,[2.61,.87,1.36,1.85,1.41,1.41,2.28],.66,17,{(1,6):GREEN,(3,6):RED})
    tx(s,'April: an almost flat benchmark still produced a loss on the ideal path.',.79,5.99,11.65,.31,17,INK,italic=True)
    foot(s,'Part 1 frozen returns · RMSC 5003 Ch. 5 · Bansal & Marshall (2015)', 'A2')
    note(s,'Each path is rebased for the episode, and durations differ. The expansion of the exposure base in the 2020 rebound dominates arithmetic reset drag. In April 2025 the terminal benchmark trend was weak and returns repeatedly reversed. Here the ideal daily reset finished below one dollar despite a positive benchmark return.')


def robustness(s, data, metrics):
    head(s,'The near-flat gap persists across windows and bands',
         'Median ideal-minus-linear return in percentage points · number of disjoint windows in parentheses',size=28.5)
    rows=[]
    for days in (10,21):
        for band in (.03,.05):
            lower, higher = [group(data, days,band,v) for v in ('Lower RMS','Higher RMS')]
            rows.append((f'{days} trading days',f'±{band:.0%}',f'{pp(lower["median"])}  ({lower["n"]})',
                         f'{pp(higher["median"])}  ({higher["n"]})'))
    book_table(s,['Return horizon','QQQ return band','Lower volatility','Higher volatility'],
               rows,.8,2.24,[2.50,2.75,2.88,3.60],.59,18,{(2,3):RED})
    tx(s,'Mean absolute gap rises with the holding period',.82,5.63,11.75,.31,17,INK,bold=True)
    tx(s,f'1 day  {metrics["holding_qqq_1_mean_abs_reset_gap"]}     ·     10 days  {metrics["holding_qqq_10_mean_abs_reset_gap"]}     ·     21 days  {metrics["holding_qqq_21_mean_abs_reset_gap"]}',
       .82,6.06,11.75,.37,18,MUTED)
    foot(s,'Descriptive ex-post groups · no forecasting interpretation · Loviscek et al. (2014) · Giannetti (2017)', 'A3')
    note(s,'For each horizon, consecutive blocks start at the first canonical observation. Direction and volatility are measured on completion of the block. The mean absolute gap below uses all overlapping holding periods as a separate unconditional check. Serial dependence and the sample sizes limit inference.')


def diagnostics(s, base, data):
    head(s,'QQQ’s unconditional tails exceed the normal benchmark',
         'Standardized daily log returns · 3 Jan 2019 to 20 Nov 2026',size=28.5)
    img = s.shapes.add_picture(str(base/'figures/part2_qqq_normal_qq.png'),Inches(.77),Inches(fit_y(s,1.99)),width=Inches(6.22))
    img.name='Normal quantile plot of QQQ standardized daily log returns'
    line(s,8.42,2.14,8.42,6.38,FAINT)
    tx(s,f'{data["excess_kurtosis_qqq_log"]:.2f}',8.82,2.49,3.36,.97,62,RED,bold=True)
    tx(s,'Excess kurtosis',8.87,3.55,3.40,.36,22,INK,bold=True)
    tx(s,'Standard normal = 0',8.88,4.04,3.41,.31,16,MUTED)
    tx(s,'Diagnose fitted residuals\nbefore choosing an\ninnovation distribution.',8.88,4.88,3.66,1.03,19,INK)
    foot(s,'RMSC 5003 Ch. 7–8 · reference line and excess kurtosis are unconditional diagnostics', 'A4')
    note(s,'The chart is the unconditional normal Q–Q diagnostic for standardized QQQ daily log returns, analogous to Chapter 8. The full-sample kurtosis is the bias-corrected Fisher estimate. Time-varying volatility can account for some unconditional excess kurtosis. Part 3 fits the conditional dynamics and checks the residuals before choosing innovations.')


def build(template: Path, base: Path, output: Path) -> None:
    """Render slides 6–7 of the original group master into the Part 2 deck."""
    data = json.loads((base / 'analysis_values.json').read_text(encoding='utf-8'))
    metrics = data['original']
    p = Presentation(template)
    divider, example = p.slides[5], p.slides[6]
    layout = divider.slide_layout
    items = p.slides._sldIdLst
    for i, item in reversed(list(enumerate(items))):
        if i not in (5, 6):
            p.part.drop_rel(item.rId)
            items.remove(item)
    divider.part.partname = PackURI('/ppt/slides/slide1.xml')
    example.part.partname = PackURI('/ppt/slides/slide2.xml')
    update_text(divider.shapes[1], 'PART 2')
    update_text(example.shapes[1], 'PART 2')
    FRAME[:] = [deepcopy(example.shapes[i]._element) for i in (*range(7), 14, 15, 16)]
    cover(divider)
    round_trip(example)
    wealth_history(new(p, layout), base, metrics)
    volatility(new(p, layout), base, data, metrics)
    losses(new(p, layout), metrics)
    funding(new(p, layout), data, metrics)
    stress(new(p, layout), metrics)
    robustness(new(p, layout), data, metrics)
    diagnostics(new(p, layout), base, data)
    p.core_properties.title = 'Return Mechanics · Part 2'
    p.core_properties.subject = 'RMSC 5003 Risk Measures · Daily resets and tail risk in TQQQ'
    p.core_properties.author = ''
    p.core_properties.last_modified_by = ''
    output.parent.mkdir(parents=True, exist_ok=True)
    p.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, required=True, help='Original group PowerPoint template')
    parser.add_argument('--input-dir', type=Path, default=PART2_ROOT, help='Core and research analysis output root')
    parser.add_argument('--output', type=Path, default=PART2_ROOT/'presentation/Part2_Presentation.pptx')
    args = parser.parse_args()
    build(args.template, args.input_dir, args.output)


if __name__=='__main__':
    main()
