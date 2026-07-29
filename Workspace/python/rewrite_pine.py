# -*- coding: utf-8 -*-
import sys

with open(r'd:\Antigravity\Workspace\python\nq_pine_arrays.txt', 'r', encoding='utf-8') as f:
    nq_arrays = f.read()

pine_content = f'''// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// (c) TradingView

//@version=6
indicator("IB Research Terminal — Hourly Levels", "IB Levels", overlay = true,
     max_lines_count  = 500,
     max_labels_count = 500,
     max_boxes_count  = 10)

// ─── INPUTS : Custom Hours ──────────────────────────────────────────────────
i_h1 = input.string("09:30", "Hour 1", options = ["None", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00"], group = "① Custom Hours")
i_h2 = input.string("10:00", "Hour 2", options = ["None", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00"], group = "① Custom Hours")
i_h3 = input.string("None", "Hour 3", options = ["None", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00"], group = "① Custom Hours")
i_h4 = input.string("None", "Hour 4", options = ["None", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00"], group = "① Custom Hours")
i_h5 = input.string("None", "Hour 5", options = ["None", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00"], group = "① Custom Hours")

// ─── INPUTS : Reach Levels ──────────────────────────────────────────────────
i_r95 = input.bool(true,  "95% Reach  (nearly always reached)", group = "② Reach Levels")
i_r90 = input.bool(false, "90% Reach",                          group = "② Reach Levels")
i_r75 = input.bool(true,  "75% Reach",                          group = "② Reach Levels")
i_r50 = input.bool(true,  "50% Reach  (median extension)",      group = "② Reach Levels")
i_r25 = input.bool(true,  "25% Reach",                          group = "② Reach Levels")
i_r10 = input.bool(false, "10% Reach",                          group = "② Reach Levels")
i_r05 = input.bool(false, "5% Reach   (stretch target)",        group = "② Reach Levels")

// ─── INPUTS : IB Settings ───────────────────────────────────────────────────
i_ibStartH = input.int(9,  "IB Start Hour (NY time)", minval = 0, maxval = 23, group = "③ IB Settings")
i_ibStartM = input.int(30, "IB Start Minute",         minval = 0, maxval = 59, group = "③ IB Settings")
i_ibDur    = input.int(60, "IB Duration (minutes)",    minval = 30, maxval = 120, group = "③ IB Settings")

// ─── INPUTS : Display ───────────────────────────────────────────────────────
i_showIB   = input.bool(true,  "Show IB Range Box", group = "④ Display")
i_lineW    = input.int(1,      "Line Width",        minval = 1, maxval = 5, group = "④ Display")
i_theme    = input.string("Dark", "Theme",        options = ["Dark", "Light"], group = "④ Display")
i_lblSize  = input.string("small", "Label Size",  options = ["tiny", "small", "normal"], group = "④ Display")

// ═══════════════════════════════════════════════════════════════════════════════
// THEME COLORS
// ═══════════════════════════════════════════════════════════════════════════════
bool isDark = i_theme == "Dark"

color C_R95 = isDark ? color.new(#34d399, 15) : color.new(#059669, 15)
color C_R90 = isDark ? color.new(#34d399, 30) : color.new(#059669, 30)
color C_R75 = isDark ? color.new(#38bdf8, 20) : color.new(#0284c7, 20)
color C_R50 = isDark ? color.new(#fbbf24, 15) : color.new(#d97706, 15)
color C_R25 = isDark ? color.new(#fb923c, 25) : color.new(#ea580c, 25)
color C_R10 = isDark ? color.new(#f87171, 35) : color.new(#dc2626, 35)
color C_R05 = isDark ? color.new(#818cf8, 30) : color.new(#6366f1, 30)

color C_IB_LINE = isDark ? color.new(#a78bfa, 25) : color.new(#7c3aed, 25)
color C_IB_BOX  = isDark ? color.new(#818cf8, 88) : color.new(#818cf8, 92)
color C_LBL_BG  = isDark ? color.new(#18181b, 5) : color.new(#f4f4f5, 5)
color C_LBL_TXT = isDark ? color.new(#e4e4e7, 0) : color.new(#27272a, 0)
color C_INFO_BG = isDark ? color.new(#27272a, 10) : color.new(#e4e4e7, 10)

var SIZE = i_lblSize == "tiny" ? size.tiny : i_lblSize == "small" ? size.small : size.normal

// ═══════════════════════════════════════════════════════════════════════════════
// DATA ARRAYS
// ═══════════════════════════════════════════════════════════════════════════════
var int[] WSTARTS = array.from(1080, 1110, 1140, 1170, 1200, 1230, 1260, 1290, 1320, 1350, 1380, 1410, 0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 390, 420, 450, 480, 510, 540, 570, 600, 630, 660, 690, 720, 750, 780, 810, 840)
var string[] WNAMES = array.from("18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00", "23:30", "00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30", "05:00", "05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00")

var ACT_PCT = array.new<int>(0)
var RLABELS = array.new<string>(0)
{nq_arrays}
    if i_r95
        array.push(ACT_PCT, 0)
        array.push(RLABELS, "95%")
    if i_r90
        array.push(ACT_PCT, 1)
        array.push(RLABELS, "90%")
    if i_r75
        array.push(ACT_PCT, 4)
        array.push(RLABELS, "75%")
    if i_r50
        array.push(ACT_PCT, 9)
        array.push(RLABELS, "50%")
    if i_r25
        array.push(ACT_PCT, 14)
        array.push(RLABELS, "25%")
    if i_r10
        array.push(ACT_PCT, 17)
        array.push(RLABELS, "10%")
    if i_r05
        array.push(ACT_PCT, 18)
        array.push(RLABELS, "5%")

getExt(int wIdx, int pIdx) =>
    int idx = wIdx * 19 + pIdx
    float val = 0.0
    if idx < array.size(NQ_EXT)
        val := array.get(NQ_EXT, idx)
    val

getClr(int pIdx) =>
    switch pIdx
        0  => C_R95
        1  => C_R90
        4  => C_R75
        9  => C_R50
        14 => C_R25
        17 => C_R10
        18 => C_R05
        => isDark ? color.new(#71717a, 40) : color.new(#a1a1aa, 40)

getStyle(int pIdx) =>
    pIdx <= 1 ? line.style_dotted : pIdx <= 9 ? line.style_dashed : line.style_solid

isWindowOn(int wIdx) =>
    string wn = array.get(WNAMES, wIdx)
    wn == i_h1 or wn == i_h2 or wn == i_h3 or wn == i_h4 or wn == i_h5

// ═══════════════════════════════════════════════════════════════════════════════
// IB DETECTION & TRACKING
// ═══════════════════════════════════════════════════════════════════════════════
int nyH   = hour(time,   "America/New_York")
int nyM   = minute(time, "America/New_York")
int nyMOD = nyH * 60 + nyM

int ibStartMOD = i_ibStartH * 60 + i_ibStartM
int ibEndMOD   = ibStartMOD + i_ibDur
int tfMin      = math.max(math.round(timeframe.in_seconds() / 60.0), 1)
int barEndMOD  = nyMOD + tfMin

bool isInIB = nyMOD < ibEndMOD and barEndMOD > ibStartMOD

var float ibHi       = na
var float ibLo       = na
var bool  ibSet      = false
var int   ibStartBar = na
var int   ibEndBar   = na
var bool  ibHiBrk    = false
var bool  ibLoBrk    = false

bool wasInIB = bar_index > 0 ? isInIB[1] : false
bool newIBStarted = isInIB and not wasInIB

if newIBStarted
    ibHi       := high
    ibLo       := low
    ibSet      := false
    ibStartBar := bar_index
    ibEndBar   := bar_index
    ibHiBrk    := false
    ibLoBrk    := false

if isInIB
    ibHi     := math.max(nz(ibHi, high), high)
    ibLo     := math.min(nz(ibLo, low),  low)
    ibEndBar := bar_index

if not isInIB and wasInIB and not na(ibHi)
    ibSet := true

if ibSet and not isInIB
    if high > ibHi
        ibHiBrk := true
    if low < ibLo
        ibLoBrk := true

bool currentShowUp = not ibLoBrk or ibHiBrk
bool currentShowDn = not ibHiBrk or ibLoBrk

// ═══════════════════════════════════════════════════════════════════════════════
// HISTORICAL INTRADAY RENDERING
// ═══════════════════════════════════════════════════════════════════════════════
var line[]  curLines  = array.new<line>(0)
var label[] curLabels = array.new<label>(0)
var box[]   curBoxes  = array.new<box>(0)

var bool lastShowUp = na
var bool lastShowDn = na

// Freeze lines when a new IB starts by abandoning the arrays
if newIBStarted
    curLines  := array.new<line>(0)
    curLabels := array.new<label>(0)
    curBoxes  := array.new<box>(0)
    lastShowUp := na
    lastShowDn := na

if ibSet and not na(ibHi) and not na(ibLo)
    float ibRange = ibHi - ibLo
    bool stateChanged = currentShowUp != lastShowUp or currentShowDn != lastShowDn or (ibSet and not ibSet[1])
    
    if stateChanged
        // Clear current active drawings to rebuild them
        if array.size(curLines) > 0
            for i = array.size(curLines) - 1 to 0
                line.delete(array.get(curLines, i))
        array.clear(curLines)
        
        if array.size(curLabels) > 0
            for i = array.size(curLabels) - 1 to 0
                label.delete(array.get(curLabels, i))
        array.clear(curLabels)
        
        if array.size(curBoxes) > 0
            for i = array.size(curBoxes) - 1 to 0
                box.delete(array.get(curBoxes, i))
        array.clear(curBoxes)
        
        // Rebuild drawings
        if i_showIB and not na(ibStartBar) and not na(ibEndBar)
            array.push(curBoxes, box.new(ibStartBar, ibHi, ibEndBar + 2, ibLo,
                 border_color = C_IB_LINE, bgcolor = C_IB_BOX,
                 border_width = 1, border_style = line.style_solid))
            
            array.push(curLines, line.new(ibEndBar, ibHi, bar_index + 1, ibHi, color = C_IB_LINE, style = line.style_solid, width = 2))
            array.push(curLines, line.new(ibEndBar, ibLo, bar_index + 1, ibLo, color = C_IB_LINE, style = line.style_solid, width = 2))
            
            array.push(curLabels, label.new(bar_index + 3, ibHi, "IB High  " + str.tostring(ibHi, format.mintick), color = C_INFO_BG, textcolor = C_LBL_TXT, style = label.style_label_left, size = SIZE))
            array.push(curLabels, label.new(bar_index + 3, ibLo, "IB Low   " + str.tostring(ibLo, format.mintick), color = C_INFO_BG, textcolor = C_LBL_TXT, style = label.style_label_left, size = SIZE))

        if ibRange > 0 and array.size(ACT_PCT) > 0
            int numPct = array.size(ACT_PCT)
            int labelOff = 5
            
            for wIdx = 0 to 40
                if not isWindowOn(wIdx)
                    continue
                
                string wn = array.get(WNAMES, wIdx)
                for p = 0 to numPct - 1
                    int pIdx   = array.get(ACT_PCT, p)
                    float rVal = getExt(wIdx, pIdx)
                    color clr  = getClr(pIdx)
                    string sty = getStyle(pIdx)
                    string rLbl = array.get(RLABELS, p)
                    string rStr = str.tostring(rVal, "#.##") + "R"
                    
                    if currentShowUp
                        float upP = ibHi + rVal * ibRange
                        array.push(curLines, line.new(ibEndBar, upP, bar_index, upP, color = clr, style = sty, width = i_lineW))
                        array.push(curLabels, label.new(bar_index + labelOff, upP, "▲ " + wn + "  " + rLbl + "  " + rStr, color = C_LBL_BG, textcolor = clr, style = label.style_label_left, size = SIZE))
                        
                    if currentShowDn
                        float dnP = ibLo - rVal * ibRange
                        array.push(curLines, line.new(ibEndBar, dnP, bar_index, dnP, color = clr, style = sty, width = i_lineW))
                        array.push(curLabels, label.new(bar_index + labelOff, dnP, "▼ " + wn + "  " + rLbl + "  " + rStr, color = C_LBL_BG, textcolor = clr, style = label.style_label_left, size = SIZE))
                    
                    labelOff += 4
                    
        string breakState = ibHiBrk and ibLoBrk ? "DOUBLE BREAK" : ibHiBrk ? "HIGH BROKEN ▲" : ibLoBrk ? "LOW BROKEN ▼" : "NO BREAK"
        color bsClr = ibHiBrk and ibLoBrk ? (isDark ? color.new(#f87171, 0) : color.new(#dc2626, 0)) : ibHiBrk ? (isDark ? color.new(#34d399, 0) : color.new(#059669, 0)) : ibLoBrk ? (isDark ? color.new(#f87171, 0) : color.new(#dc2626, 0)) : (isDark ? color.new(#71717a, 0) : color.new(#a1a1aa, 0))
        float midIB = (ibHi + ibLo) / 2
        array.push(curLabels, label.new(bar_index + 3, midIB, breakState, color = C_INFO_BG, textcolor = bsClr, style = label.style_label_left, size = SIZE))

        lastShowUp := currentShowUp
        lastShowDn := currentShowDn

    // Dynamically extend active lines/labels to the current bar if no new breaks occurred
    if not stateChanged
        if array.size(curLines) > 0
            for i = 0 to array.size(curLines) - 1
                line.set_x2(array.get(curLines, i), bar_index)
        if array.size(curLabels) > 0
            for i = 0 to array.size(curLabels) - 1
                lbl = array.get(curLabels, i)
                int old_x = label.get_x(lbl)
                if barstate.isnew
                    label.set_x(lbl, old_x + 1)
'''

with open(r'd:\Antigravity\Indicators\ib_hourly_levels.pine', 'w', encoding='utf-8') as f:
    f.write(pine_content)

print("Pine script fully rewritten and updated!")
