/** @odoo-module */

/**
 * 判斷顏色是否為淺色（用於決定文字顏色）
 * 支援 Hex 和 HSL 格式
 * @param {string} color - Hex color string (e.g., "#ffffff") or HSL string (e.g., "hsl(180, 70%, 50%)")
 * @returns {boolean} - True if the color is light, false otherwise
 */
export function isLightColor(color) {
  if (!color || typeof color !== 'string') return false;

  // Handle HSL format: hsl(hue, saturation%, lightness%)
  const hslMatch = color.match(/hsl\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*\)/i);
  if (hslMatch) {
    const lightness = parseInt(hslMatch[3], 10);
    // Lightness > 50% is considered light
    return lightness > 50;
  }

  // Handle Hex format
  const hex = color.replace('#', '');
  if (hex.length !== 6) return false;
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5;
}
