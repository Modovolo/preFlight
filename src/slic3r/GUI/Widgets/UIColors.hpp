///|/ Copyright (c) preFlight 2025+ oozeBot, LLC
///|/
///|/ preFlight is based on PrusaSlicer and released under AGPLv3 or higher
///|/
#ifndef slic3r_UI_Colors_hpp_
#define slic3r_UI_Colors_hpp_

#include <wx/colour.h>

#include "../ThemePalette.hpp" // preFlight: data-driven dark palette (active_palette())

// ============================================================================
// Widget UI Colors - Centralized color definitions for preFlight widgets
// ============================================================================
//
// ARCHITECTURE:
// - All colors are defined as Dark/Light pairs (building blocks)
// - Unified accessor functions return the correct color based on current theme
// - Callers should ALWAYS use unified accessors, NEVER check dark_mode() themselves
//
// DARK THEME: GitHub-inspired cool blue-gray palette
//   #0D1117 (13,17,23)   - deepest background (panels, canvas)
//   #161B22 (22,27,34)   - secondary background (inputs, headers)
//   #21262D (33,38,45)   - elevated/hover states
//   #30363D (48,54,61)   - borders, dividers
//   #C9D1D9 (201,209,217) - primary text
//   #8B949E (139,148,158) - secondary text
//   #6E7681 (110,118,129) - muted/disabled text
//
// USAGE:
//   control->SetBackgroundColour(UIColors::InputBackground());  // Correct!
//   control->SetForegroundColour(UIColors::PanelForeground());  // Correct!
//
// NEVER DO THIS:
//   if (dark_mode())
//       control->SetBackgroundColour(UIColors::InputBackgroundDark());
//   else
//       control->SetBackgroundColour(UIColors::InputBackgroundLight());
//
// ============================================================================

// Forward declaration - defined in GUI_App.cpp
// This avoids circular includes while allowing UIColors to check theme state
namespace Slic3r
{
namespace GUI
{
bool IsDarkMode();
}
} // namespace Slic3r

// preFlight: pack a wxColour into a 0xRRGGBB int for StateColor (which takes packed ints).
inline int wxcolour_to_rgb_int(const wxColour &c)
{
    return (c.Red() << 16) | (c.Green() << 8) | c.Blue();
}
inline int accent_primary_rgb()
{
    return wxcolour_to_rgb_int(Slic3r::GUI::active_palette().accent_primary);
}
inline int accent_hover_rgb()
{
    return wxcolour_to_rgb_int(Slic3r::GUI::active_palette().accent_hover);
}

// Legacy static constants (for backward compatibility during transition)
static const int clr_border_normal = 0x30363D; // GitHub border
inline int clr_border_hovered()
{
    return accent_primary_rgb();
} // themed accent
static const int clr_border_disabled = 0x30363D;

static const int clr_background_normal_light = 0xFFFDF8; // Warm white (255,253,248)
static const int clr_background_normal_dark = 0x161B22;  // GitHub #161B22 (22,27,34)
inline int clr_background_focused()
{
    return accent_primary_rgb();
} // themed accent
static const int clr_background_disabled_dark = 0x21262D;  // GitHub #21262D (33,38,45)
static const int clr_background_disabled_light = 0xEBE8E4; // Warm light disabled

static const int clr_foreground_normal = 0x262E30;
inline int clr_foreground_focused()
{
    return accent_primary_rgb();
} // themed accent
static const int clr_foreground_disabled = 0x909090;
static const int clr_foreground_disabled_dark = 0x6E7681; // GitHub muted #6E7681
static const int clr_foreground_disabled_light = 0x909090;

// ============================================================================
// UIColors Namespace - Theme Color API
// ============================================================================

namespace UIColors
{

// ============================================================================
// SECTION 1: Building Blocks - Dark/Light specific colors
// ============================================================================
// These define the actual color values. Use unified accessors below instead.
// ============================================================================

// --- Input Field Colors (Building Blocks) ---

inline wxColour InputBackgroundDark()
{
    return Slic3r::GUI::active_palette().input_background;
}
inline wxColour InputBackgroundLight()
{
    return Slic3r::GUI::active_palette().input_background;
}
inline wxColour InputBackgroundDisabledDark()
{
    return Slic3r::GUI::active_palette().input_background_disabled;
}
inline wxColour InputBackgroundDisabledLight()
{
    return Slic3r::GUI::active_palette().input_background_disabled;
}

inline wxColour InputForegroundDark()
{
    return Slic3r::GUI::active_palette().input_foreground;
}
inline wxColour InputForegroundLight()
{
    return Slic3r::GUI::active_palette().input_foreground;
}
inline wxColour InputForegroundDisabledDark()
{
    return Slic3r::GUI::active_palette().input_foreground_disabled;
}
inline wxColour InputForegroundDisabledLight()
{
    return Slic3r::GUI::active_palette().input_foreground_disabled;
}

// --- Panel/Background Colors (Building Blocks) ---

inline wxColour PanelBackgroundDark()
{
    return Slic3r::GUI::active_palette().panel_background;
}
inline wxColour PanelBackgroundLight()
{
    return Slic3r::GUI::active_palette().panel_background;
}
inline wxColour PanelForegroundDark()
{
    return Slic3r::GUI::active_palette().panel_foreground;
}
inline wxColour PanelForegroundLight()
{
    return Slic3r::GUI::active_palette().panel_foreground;
}

// --- Content Area Colors (Building Blocks) ---
// Content areas (collapsible sections, info panels, static box interiors)
// Use the lighter interior color, not the darkest page background

inline wxColour ContentBackgroundDark()
{
    return Slic3r::GUI::active_palette().content_background;
}
inline wxColour ContentBackgroundLight()
{
    return Slic3r::GUI::active_palette().content_background;
}
inline wxColour ContentForegroundDark()
{
    return Slic3r::GUI::active_palette().content_foreground;
}
inline wxColour ContentForegroundLight()
{
    return Slic3r::GUI::active_palette().content_foreground;
}

// --- Secondary/Badge Text Colors (Building Blocks) ---

inline wxColour SecondaryTextDark()
{
    return Slic3r::GUI::active_palette().secondary_text;
}
inline wxColour SecondaryTextLight()
{
    return Slic3r::GUI::active_palette().secondary_text;
}

// --- Label/Text Colors (Building Blocks) ---

inline wxColour LabelDefaultDark()
{
    return Slic3r::GUI::active_palette().label_default;
}
inline wxColour LabelDefaultLight()
{
    return Slic3r::GUI::active_palette().label_default;
}
inline wxColour HighlightLabelDark()
{
    return Slic3r::GUI::active_palette().highlight_label;
}
inline wxColour HighlightLabelLight()
{
    return Slic3r::GUI::active_palette().highlight_label;
}
inline wxColour HighlightBackgroundDark()
{
    return Slic3r::GUI::active_palette().highlight_background;
}
inline wxColour HighlightBackgroundLight()
{
    return Slic3r::GUI::active_palette().highlight_background;
}

// --- Button Label Colors (Building Blocks) ---

inline wxColour HoveredBtnLabelDark()
{
    return Slic3r::GUI::active_palette().hovered_btn_label;
}
inline wxColour HoveredBtnLabelLight()
{
    return Slic3r::GUI::active_palette().hovered_btn_label;
}
inline wxColour DefaultBtnLabelDark()
{
    return Slic3r::GUI::active_palette().default_btn_label;
}
inline wxColour DefaultBtnLabelLight()
{
    return Slic3r::GUI::active_palette().default_btn_label;
}
inline wxColour SelectedBtnBackgroundDark()
{
    return Slic3r::GUI::active_palette().selected_btn_background;
}
inline wxColour SelectedBtnBackgroundLight()
{
    return Slic3r::GUI::active_palette().selected_btn_background;
}

// --- Header/List Colors (Building Blocks) ---

inline wxColour HeaderBackgroundDark()
{
    return Slic3r::GUI::active_palette().header_background;
}
inline wxColour HeaderBackgroundLight()
{
    return Slic3r::GUI::active_palette().header_background;
}
inline wxColour HeaderHoverDark()
{
    return Slic3r::GUI::active_palette().header_hover;
}
inline wxColour HeaderHoverLight()
{
    return Slic3r::GUI::active_palette().header_hover;
}
// Top-level section headers (slightly darker than regular headers for visual hierarchy)
inline wxColour SectionHeaderBackgroundDark()
{
    return Slic3r::GUI::active_palette().section_header_background;
}
inline wxColour SectionHeaderBackgroundLight()
{
    return Slic3r::GUI::active_palette().section_header_background;
}
inline wxColour SectionHeaderHoverDark()
{
    return Slic3r::GUI::active_palette().section_header_hover;
}
inline wxColour SectionHeaderHoverLight()
{
    return Slic3r::GUI::active_palette().section_header_hover;
}

inline wxColour HeaderDividerDark()
{
    return Slic3r::GUI::active_palette().header_divider;
}
inline wxColour HeaderDividerLight()
{
    return Slic3r::GUI::active_palette().header_divider;
}

// --- Tab Bar Colors (Building Blocks) ---

inline wxColour TabBackgroundNormalDark()
{
    return Slic3r::GUI::active_palette().tab_background_normal;
}
inline wxColour TabBackgroundNormalLight()
{
    return Slic3r::GUI::active_palette().tab_background_normal;
}
inline wxColour TabBackgroundHoverDark()
{
    return Slic3r::GUI::active_palette().tab_background_hover;
}
inline wxColour TabBackgroundHoverLight()
{
    return Slic3r::GUI::active_palette().tab_background_hover;
}
inline wxColour TabBackgroundSelectedDark()
{
    return Slic3r::GUI::active_palette().tab_background_selected;
}
inline wxColour TabBackgroundSelectedLight()
{
    return Slic3r::GUI::active_palette().tab_background_selected;
}
inline wxColour TabBackgroundDisabledDark()
{
    return Slic3r::GUI::active_palette().tab_background_disabled;
}
inline wxColour TabBackgroundDisabledLight()
{
    return Slic3r::GUI::active_palette().tab_background_disabled;
}
inline wxColour TabTextNormalDark()
{
    return Slic3r::GUI::active_palette().tab_text_normal;
}
inline wxColour TabTextNormalLight()
{
    return Slic3r::GUI::active_palette().tab_text_normal;
}
inline wxColour TabTextSelectedDark()
{
    return Slic3r::GUI::active_palette().tab_text_selected;
}
inline wxColour TabTextSelectedLight()
{
    return Slic3r::GUI::active_palette().tab_text_selected;
}
inline wxColour TabTextDisabledDark()
{
    return Slic3r::GUI::active_palette().tab_text_disabled;
}
inline wxColour TabTextDisabledLight()
{
    return Slic3r::GUI::active_palette().tab_text_disabled;
}
inline wxColour TabBorderDark()
{
    return Slic3r::GUI::active_palette().tab_border;
}
inline wxColour TabBorderLight()
{
    return Slic3r::GUI::active_palette().tab_border;
}

// --- StaticBox Border Colors (Building Blocks) ---

inline wxColour StaticBoxBorderDark()
{
    return Slic3r::GUI::active_palette().static_box_border;
}
inline wxColour StaticBoxBorderLight()
{
    return Slic3r::GUI::active_palette().static_box_border;
}

// --- FlatStaticBox (Section Group) Border Colors ---

inline wxColour SectionBorderDark()
{
    return Slic3r::GUI::active_palette().section_border;
}
inline wxColour SectionBorderLight()
{
    return Slic3r::GUI::active_palette().section_border;
}

// --- Accent Colors (themed; default to preFlight orange when a theme omits them) ---

inline wxColour AccentPrimary()
{
    return Slic3r::GUI::active_palette().accent_primary;
}
inline wxColour AccentHover()
{
    return Slic3r::GUI::active_palette().accent_hover;
}
inline wxColour AccentDark()
{
    return Slic3r::GUI::active_palette().accent_dark;
}
inline wxColour AccentSecondary()
{
    return Slic3r::GUI::active_palette().accent_secondary;
}
inline wxColour AccentText()
{
    return Slic3r::GUI::active_palette().accent_text;
}

// --- Semantic status colors (themed) ---

inline wxColour Error()
{
    return Slic3r::GUI::active_palette().error;
}
inline wxColour Warning()
{
    return Slic3r::GUI::active_palette().warning;
}

// ============================================================================
// SECTION 2: Unified Accessors - USE THESE!
// ============================================================================
// These automatically return the correct color for the current theme.
// All widget code should use these functions exclusively.
// ============================================================================

// --- Input Field Colors ---

inline wxColour InputBackground()
{
    return Slic3r::GUI::IsDarkMode() ? InputBackgroundDark() : InputBackgroundLight();
}

inline wxColour InputBackgroundDisabled()
{
    return Slic3r::GUI::IsDarkMode() ? InputBackgroundDisabledDark() : InputBackgroundDisabledLight();
}

inline wxColour InputForeground()
{
    return Slic3r::GUI::IsDarkMode() ? InputForegroundDark() : InputForegroundLight();
}

inline wxColour InputForegroundDisabled()
{
    return Slic3r::GUI::IsDarkMode() ? InputForegroundDisabledDark() : InputForegroundDisabledLight();
}

// --- Panel Colors ---

inline wxColour PanelBackground()
{
    return Slic3r::GUI::IsDarkMode() ? PanelBackgroundDark() : PanelBackgroundLight();
}

inline wxColour PanelForeground()
{
    return Slic3r::GUI::IsDarkMode() ? PanelForegroundDark() : PanelForegroundLight();
}

// --- Content Area Colors ---

inline wxColour ContentBackground()
{
    return Slic3r::GUI::IsDarkMode() ? ContentBackgroundDark() : ContentBackgroundLight();
}

inline wxColour ContentForeground()
{
    return Slic3r::GUI::IsDarkMode() ? ContentForegroundDark() : ContentForegroundLight();
}

// --- Secondary Text ---

inline wxColour SecondaryText()
{
    return Slic3r::GUI::IsDarkMode() ? SecondaryTextDark() : SecondaryTextLight();
}

// --- Labels ---

inline wxColour LabelDefault()
{
    return Slic3r::GUI::IsDarkMode() ? LabelDefaultDark() : LabelDefaultLight();
}

inline wxColour HighlightLabel()
{
    return Slic3r::GUI::IsDarkMode() ? HighlightLabelDark() : HighlightLabelLight();
}

inline wxColour HighlightBackground()
{
    return Slic3r::GUI::IsDarkMode() ? HighlightBackgroundDark() : HighlightBackgroundLight();
}

// --- Button Labels ---

inline wxColour HoveredBtnLabel()
{
    return Slic3r::GUI::IsDarkMode() ? HoveredBtnLabelDark() : HoveredBtnLabelLight();
}

inline wxColour DefaultBtnLabel()
{
    return Slic3r::GUI::IsDarkMode() ? DefaultBtnLabelDark() : DefaultBtnLabelLight();
}

inline wxColour SelectedBtnBackground()
{
    return Slic3r::GUI::IsDarkMode() ? SelectedBtnBackgroundDark() : SelectedBtnBackgroundLight();
}

// --- Headers ---

inline wxColour HeaderBackground()
{
    return Slic3r::GUI::IsDarkMode() ? HeaderBackgroundDark() : HeaderBackgroundLight();
}

inline wxColour HeaderHover()
{
    return Slic3r::GUI::IsDarkMode() ? HeaderHoverDark() : HeaderHoverLight();
}

inline wxColour HeaderDivider()
{
    return Slic3r::GUI::IsDarkMode() ? HeaderDividerDark() : HeaderDividerLight();
}

// --- Tab Bar ---

inline wxColour TabBackgroundNormal()
{
    return Slic3r::GUI::IsDarkMode() ? TabBackgroundNormalDark() : TabBackgroundNormalLight();
}

inline wxColour TabBackgroundHover()
{
    return Slic3r::GUI::IsDarkMode() ? TabBackgroundHoverDark() : TabBackgroundHoverLight();
}

inline wxColour TabBackgroundSelected()
{
    return Slic3r::GUI::IsDarkMode() ? TabBackgroundSelectedDark() : TabBackgroundSelectedLight();
}

inline wxColour TabBackgroundDisabled()
{
    return Slic3r::GUI::IsDarkMode() ? TabBackgroundDisabledDark() : TabBackgroundDisabledLight();
}

inline wxColour TabTextNormal()
{
    return Slic3r::GUI::IsDarkMode() ? TabTextNormalDark() : TabTextNormalLight();
}

inline wxColour TabTextSelected()
{
    return Slic3r::GUI::IsDarkMode() ? TabTextSelectedDark() : TabTextSelectedLight();
}

inline wxColour TabTextDisabled()
{
    return Slic3r::GUI::IsDarkMode() ? TabTextDisabledDark() : TabTextDisabledLight();
}

inline wxColour TabBorder()
{
    return Slic3r::GUI::IsDarkMode() ? TabBorderDark() : TabBorderLight();
}

inline wxColour StaticBoxBorder()
{
    return Slic3r::GUI::IsDarkMode() ? StaticBoxBorderDark() : StaticBoxBorderLight();
}

inline wxColour SectionBorder()
{
    return Slic3r::GUI::IsDarkMode() ? SectionBorderDark() : SectionBorderLight();
}

// ============================================================================
// SECTION 3: Canvas / 3D View Colors
// ============================================================================
// These colors are used for the OpenGL canvas, bed/platter, and grid.
// Convert to ColorRGBA in calling code: ColorRGBA(r/255.0f, g/255.0f, b/255.0f, 1.0f)
// ============================================================================

// --- Canvas Background (area around the bed) ---
// Slightly lighter than toolbar to create contrast

inline wxColour CanvasBackgroundDark()
{
    return Slic3r::GUI::active_palette().canvas_background;
}
inline wxColour CanvasBackgroundLight()
{
    return Slic3r::GUI::active_palette().canvas_background;
}

// --- Canvas Gradient Top (lighter part of background gradient) ---
// Slightly lighter still at top for subtle depth

inline wxColour CanvasGradientTopDark()
{
    return Slic3r::GUI::active_palette().canvas_gradient_top;
}
inline wxColour CanvasGradientTopLight()
{
    return Slic3r::GUI::active_palette().canvas_gradient_top;
}

// --- Bed/Platter Surface ---

inline wxColour BedSurfaceDark()
{
    return Slic3r::GUI::active_palette().bed_surface;
}
inline wxColour BedSurfaceLight()
{
    return Slic3r::GUI::active_palette().bed_surface;
}

// --- Bed Grid Lines ---

inline wxColour BedGridDark()
{
    return Slic3r::GUI::active_palette().bed_grid;
}
inline wxColour BedGridLight()
{
    return Slic3r::GUI::active_palette().bed_grid;
}

// --- Menu Bar Background ---

inline wxColour MenuBackgroundDark()
{
    return Slic3r::GUI::active_palette().menu_background;
}
inline wxColour MenuBackgroundLight()
{
    return Slic3r::GUI::active_palette().menu_background;
}

inline wxColour MenuHoverDark()
{
    return Slic3r::GUI::active_palette().menu_hover;
}
inline wxColour MenuHoverLight()
{
    return Slic3r::GUI::active_palette().menu_hover;
}

inline wxColour MenuTextDark()
{
    return Slic3r::GUI::active_palette().menu_text;
}
inline wxColour MenuTextLight()
{
    return Slic3r::GUI::active_palette().menu_text;
}

// --- Window Title Bar Colors (Windows 11 custom caption) ---
// Title bar is darkest layer to create visual hierarchy with menu/toolbar

inline wxColour TitleBarBackgroundDark()
{
    return Slic3r::GUI::active_palette().title_bar_background;
}
inline wxColour TitleBarBackgroundLight()
{
    return Slic3r::GUI::active_palette().title_bar_background;
}
inline wxColour TitleBarTextDark()
{
    return Slic3r::GUI::active_palette().title_bar_text;
}
inline wxColour TitleBarTextLight()
{
    return Slic3r::GUI::active_palette().title_bar_text;
}
inline wxColour TitleBarBorderDark()
{
    return Slic3r::GUI::active_palette().title_bar_border;
}
inline wxColour TitleBarBorderLight()
{
    return Slic3r::GUI::active_palette().title_bar_border;
}

// --- Legend Combo Box Colors (ImGui combo in Preview legend) ---
// These need alpha support, so we provide both RGB values and alpha separately

inline wxColour LegendComboBackgroundDark()
{
    return Slic3r::GUI::active_palette().legend_combo_background;
}
inline wxColour LegendComboBackgroundLight()
{
    return Slic3r::GUI::active_palette().legend_combo_background;
}
inline wxColour LegendComboBackgroundHoveredDark()
{
    return Slic3r::GUI::active_palette().legend_combo_background_hovered;
}
inline wxColour LegendComboBackgroundHoveredLight()
{
    return Slic3r::GUI::active_palette().legend_combo_background_hovered;
}

// --- Canvas Unified Accessors ---

inline wxColour CanvasBackground()
{
    return Slic3r::GUI::IsDarkMode() ? CanvasBackgroundDark() : CanvasBackgroundLight();
}

inline wxColour CanvasGradientTop()
{
    return Slic3r::GUI::IsDarkMode() ? CanvasGradientTopDark() : CanvasGradientTopLight();
}

inline wxColour BedSurface()
{
    return Slic3r::GUI::IsDarkMode() ? BedSurfaceDark() : BedSurfaceLight();
}

inline wxColour BedGrid()
{
    return Slic3r::GUI::IsDarkMode() ? BedGridDark() : BedGridLight();
}

inline wxColour MenuBackground()
{
    return Slic3r::GUI::IsDarkMode() ? MenuBackgroundDark() : MenuBackgroundLight();
}

inline wxColour MenuHover()
{
    return Slic3r::GUI::IsDarkMode() ? MenuHoverDark() : MenuHoverLight();
}

inline wxColour MenuText()
{
    return Slic3r::GUI::IsDarkMode() ? MenuTextDark() : MenuTextLight();
}

inline wxColour TitleBarBackground()
{
    return Slic3r::GUI::IsDarkMode() ? TitleBarBackgroundDark() : TitleBarBackgroundLight();
}

inline wxColour TitleBarText()
{
    return Slic3r::GUI::IsDarkMode() ? TitleBarTextDark() : TitleBarTextLight();
}

inline wxColour TitleBarBorder()
{
    return Slic3r::GUI::IsDarkMode() ? TitleBarBorderDark() : TitleBarBorderLight();
}

// --- Legend Combo Box ---

inline wxColour LegendComboBackground()
{
    return Slic3r::GUI::IsDarkMode() ? LegendComboBackgroundDark() : LegendComboBackgroundLight();
}

inline wxColour LegendComboBackgroundHovered()
{
    return Slic3r::GUI::IsDarkMode() ? LegendComboBackgroundHoveredDark() : LegendComboBackgroundHoveredLight();
}

// Alpha value for legend combo (0.0-1.0 for ImGui)
inline float LegendComboAlpha()
{
    return 0.95f;
}

// ============================================================================
// SECTION 4: Preview Slider/Ruler Colors (ImGui)
// ============================================================================
// These are used for the vertical/horizontal layer sliders and rulers in Preview.
// Return raw RGB values for ImGui (0.0-1.0 scale).
// ============================================================================

// --- Preview Ruler Background (semi-transparent overlay) ---

inline void RulerBackgroundRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().ruler_background;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- Legend/GCode Window Background ---

inline void LegendWindowBackgroundRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().legend_window_background;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- Slider Groove Background (the track thumbs slide along) ---

inline void SliderGrooveBackgroundRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().slider_groove;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- Slider Border (outline around the groove) ---

inline void SliderBorderRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().slider_border;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- Ruler Tick Marks (the small lines on the ruler) ---

inline void RulerTickRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().ruler_tick;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- Slider Label Background (the tooltip-style label showing current value) ---

inline void SliderLabelBackgroundRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().slider_label_background;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- Legend/GCode Text Color (for value text in legends and g-code viewer) ---

inline void LegendTextRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().legend_text;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- GCode Comment Color (lighter gray for comments) ---

inline void GCodeCommentRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().gcode_comment;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

// --- GCode Command Color (G/M command tokens in the preview legend) ---

inline void GCodeCommandRGBA(float &r, float &g, float &b, float &a)
{
    const Slic3r::GUI::RGBAf &c = Slic3r::GUI::active_palette().gcode_command;
    r = c.r;
    g = c.g;
    b = c.b;
    a = c.a;
}

} // namespace UIColors

// ============================================================================
// Windows COLORREF Namespace - For Win32 API code (DarkMode.cpp, etc.)
// ============================================================================

#ifdef _WIN32
#include <windows.h>

namespace UIColorsWin
{

// preFlight: convert a palette wxColour token to a Win32 COLORREF (single source of truth).
inline COLORREF to_colorref(const wxColour &c)
{
    return RGB(c.Red(), c.Green(), c.Blue());
}

// ============================================================================
// Building Blocks (Dark/Light specific)
// ============================================================================

inline COLORREF InputBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().input_background);
}
inline COLORREF InputBackgroundLight()
{
    return to_colorref(Slic3r::GUI::active_palette().input_background);
}
inline COLORREF InputBackgroundDisabledDark()
{
    return to_colorref(Slic3r::GUI::active_palette().input_background_disabled);
}
inline COLORREF InputBackgroundDisabledLight()
{
    return to_colorref(Slic3r::GUI::active_palette().input_background_disabled);
}

inline COLORREF TextDark()
{
    return to_colorref(Slic3r::GUI::active_palette().label_default);
}
inline COLORREF TextLight()
{
    return to_colorref(Slic3r::GUI::active_palette().label_default);
}
inline COLORREF TextDisabledDark()
{
    return to_colorref(Slic3r::GUI::active_palette().input_foreground_disabled);
}
inline COLORREF TextDisabledLight()
{
    return to_colorref(Slic3r::GUI::active_palette().input_foreground_disabled);
}

inline COLORREF HeaderBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().header_background);
}
inline COLORREF HeaderBackgroundLight()
{
    return to_colorref(Slic3r::GUI::active_palette().header_background);
}
inline COLORREF HeaderDividerDark()
{
    return to_colorref(Slic3r::GUI::active_palette().header_divider);
}
inline COLORREF HeaderDividerLight()
{
    return to_colorref(Slic3r::GUI::active_palette().header_divider);
}

inline COLORREF SelectionBorderDark()
{
    return to_colorref(Slic3r::GUI::active_palette().section_border);
}
inline COLORREF SelectionBorderLight()
{
    return to_colorref(Slic3r::GUI::active_palette().section_border);
}

inline COLORREF AccentPrimary()
{
    return to_colorref(Slic3r::GUI::active_palette().accent_primary);
}

inline COLORREF SofterBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().highlight_background);
}
inline COLORREF WindowBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().panel_background);
}
inline COLORREF WindowTextDark()
{
    return to_colorref(Slic3r::GUI::active_palette().label_default);
}

inline COLORREF MenuBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().menu_background);
}
inline COLORREF MenuBackgroundLight()
{
    return to_colorref(Slic3r::GUI::active_palette().menu_background);
}
inline COLORREF MenuHotBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().menu_hover);
}
inline COLORREF MenuHotBackgroundLight()
{
    return to_colorref(Slic3r::GUI::active_palette().menu_hover);
}
inline COLORREF MenuTextDark()
{
    return to_colorref(Slic3r::GUI::active_palette().menu_text);
}
inline COLORREF MenuTextLight()
{
    return to_colorref(Slic3r::GUI::active_palette().menu_text);
}
inline COLORREF MenuDisabledTextDark()
{
    return to_colorref(Slic3r::GUI::active_palette().input_foreground_disabled);
}
inline COLORREF MenuDisabledTextLight()
{
    return to_colorref(Slic3r::GUI::active_palette().input_foreground_disabled);
}

inline COLORREF StaticBoxBorderDark()
{
    return to_colorref(Slic3r::GUI::active_palette().static_box_border);
}
inline COLORREF StaticBoxBorderLight()
{
    return to_colorref(Slic3r::GUI::active_palette().static_box_border);
}

// --- Window Title Bar Colors (Windows 11 custom caption) ---
// Title bar is darkest layer to create visual hierarchy with menu/toolbar

inline COLORREF TitleBarBackgroundDark()
{
    return to_colorref(Slic3r::GUI::active_palette().title_bar_background);
}
inline COLORREF TitleBarBackgroundLight()
{
    return to_colorref(Slic3r::GUI::active_palette().title_bar_background);
}
inline COLORREF TitleBarTextDark()
{
    return to_colorref(Slic3r::GUI::active_palette().title_bar_text);
}
inline COLORREF TitleBarTextLight()
{
    return to_colorref(Slic3r::GUI::active_palette().title_bar_text);
}
inline COLORREF TitleBarBorderDark()
{
    return to_colorref(Slic3r::GUI::active_palette().title_bar_border);
}
inline COLORREF TitleBarBorderLight()
{
    return to_colorref(Slic3r::GUI::active_palette().title_bar_border);
}

// ============================================================================
// Unified Accessors
// ============================================================================

inline COLORREF InputBackground()
{
    return Slic3r::GUI::IsDarkMode() ? InputBackgroundDark() : InputBackgroundLight();
}

inline COLORREF InputBackgroundDisabled()
{
    return Slic3r::GUI::IsDarkMode() ? InputBackgroundDisabledDark() : InputBackgroundDisabledLight();
}

inline COLORREF Text()
{
    return Slic3r::GUI::IsDarkMode() ? TextDark() : TextLight();
}

inline COLORREF TextDisabled()
{
    return Slic3r::GUI::IsDarkMode() ? TextDisabledDark() : TextDisabledLight();
}

inline COLORREF HeaderBackground()
{
    return Slic3r::GUI::IsDarkMode() ? HeaderBackgroundDark() : HeaderBackgroundLight();
}

inline COLORREF HeaderDivider()
{
    return Slic3r::GUI::IsDarkMode() ? HeaderDividerDark() : HeaderDividerLight();
}

inline COLORREF SelectionBorder()
{
    return Slic3r::GUI::IsDarkMode() ? SelectionBorderDark() : SelectionBorderLight();
}

inline COLORREF StaticBoxBorder()
{
    return Slic3r::GUI::IsDarkMode() ? StaticBoxBorderDark() : StaticBoxBorderLight();
}

inline COLORREF MenuBackground()
{
    return Slic3r::GUI::IsDarkMode() ? MenuBackgroundDark() : MenuBackgroundLight();
}

inline COLORREF MenuHotBackground()
{
    return Slic3r::GUI::IsDarkMode() ? MenuHotBackgroundDark() : MenuHotBackgroundLight();
}

inline COLORREF MenuText()
{
    return Slic3r::GUI::IsDarkMode() ? MenuTextDark() : MenuTextLight();
}

inline COLORREF MenuDisabledText()
{
    return Slic3r::GUI::IsDarkMode() ? MenuDisabledTextDark() : MenuDisabledTextLight();
}

inline COLORREF TitleBarBackground()
{
    return Slic3r::GUI::IsDarkMode() ? TitleBarBackgroundDark() : TitleBarBackgroundLight();
}

inline COLORREF TitleBarText()
{
    return Slic3r::GUI::IsDarkMode() ? TitleBarTextDark() : TitleBarTextLight();
}

inline COLORREF TitleBarBorder()
{
    return Slic3r::GUI::IsDarkMode() ? TitleBarBorderDark() : TitleBarBorderLight();
}

} // namespace UIColorsWin

#endif // _WIN32

#endif // !slic3r_UI_Colors_hpp_
