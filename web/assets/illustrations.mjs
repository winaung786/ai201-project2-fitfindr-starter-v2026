// Decorative garment illustrations, not photographs of the sample listings.
const palettes = {
  black: ["#343532", "#252822"], navy: ["#34495b", "#233746"], burgundy: ["#86524c", "#643e3b"],
  white: ["#f9f6ed", "#dbd8ca"], cream: ["#ece6d7", "#c5baa4"], green: ["#65745b", "#465d42"],
  brown: ["#987352", "#6d523c"], pink: ["#e2b8b7", "#c88c8d"], khaki: ["#b7ad8c", "#8e8464"],
  blue: ["#6f8792", "#496775"], grey: ["#969991", "#70766d"], rust: ["#b5764c", "#8e5939"]
};
let illustrationSequence = 0;
function palette(item) {
  const colors = (item.colors ?? []).join(" ").toLowerCase();
  return Object.entries(palettes).find(([key]) => colors.includes(key))?.[1] ?? palettes.cream;
}
export function garmentArt(item, compact = false) {
  const [base, dark] = palette(item), title = (item.title ?? "").toLowerCase();
  let art;
  if (item.category === "shoes") {
    const boots = /boot/.test(title);
    art = boots ? `<path d="M91 57h51l-5 96 41 24q19 8 16 24H68v-24l15-22z" fill="url(#fabric)" stroke="${dark}" stroke-width="2"/><path d="M67 199h128v11H67z" fill="#4e493e"/><path d="M104 71v82" fill="none" stroke="${dark}" stroke-width="2"/><path d="M104 153q-7 12-9 27" fill="none" stroke="${dark}" stroke-width="2"/>`
      : `<g transform="translate(8 -8) rotate(-12 130 145)"><path d="M52 119l37-39 36 13 15 42 45 23q24 7 27 27H48q-11-29 4-66z" fill="url(#fabric)" stroke="${dark}" stroke-width="2"/><path d="M45 177q52 13 167 1v21H45z" fill="#e7e3d7" stroke="#c7c3b6" stroke-width="2"/><path d="M92 93l33 42 31 13" fill="none" stroke="${dark}" stroke-width="2"/><path d="M83 116l39-4m-32 15l39-4m-30 15l37-5" stroke="#b2aa96" stroke-width="4" stroke-linecap="round"/><path d="M53 128l9 42m113-14q-17 3-22 22" fill="none" stroke="${dark}" stroke-opacity=".35" stroke-width="2"/><path d="M69 188h119" stroke="#b5b1a3" stroke-width="2"/></g>`;
  } else if (item.category === "bottoms") {
    const denim = /jean|denim/.test(title), short = /short/.test(title);
    art = `<path d="M79 47h103l5 ${short ? "103" : "165"}-51 3-8-${short ? "72" : "123"}-9 ${short ? "72" : "123"}-50-4z" fill="${denim ? "#668291" : "url(#fabric)"}" stroke="${denim ? "#4f6d7d" : dark}" stroke-width="2"/><path d="M78 63h106m-53-15v41l-5 13m-45-33q12 29 29 22m68-22q-10 29-26 22" stroke="${denim ? "#d6c8aa" : dark}" stroke-width="1.7" fill="none"/><path d="M95 51v12m68-12v12m-50-12v11m35-11v11" stroke="${denim ? "#425f6f" : dark}" stroke-width="4"/><circle cx="133" cy="55" r="3" fill="#c1ab79"/><path d="M80 ${short ? "139" : "201"}l40 4m19-1l39-3" stroke="${denim ? "#3f6275" : dark}" stroke-opacity=".6" stroke-width="2"/>`;
  } else {
    const long = /long|henley|sweat|cardigan|hoodie/.test(title), button = /henley|polo|button/.test(title);
    art = `<path d="M101 53l-37 18-${long ? "29 93 24 8 30-67" : "27 42 26 17 20-26"}v105h94V${long ? "103l30 69 24-8-29-93" : "104l20 26 26-17-27-42"}l-37-18q-16 17-31 0z" fill="url(#fabric)" stroke="${dark}" stroke-width="1.8" stroke-linejoin="round"/><path d="M101 53q30 40 62 0m-62 0q29 22 62 0" fill="none" stroke="${dark}" stroke-width="3"/><path d="M92 201h80m-79-106l4 87m72-87-4 87" fill="none" stroke="${dark}" stroke-opacity=".2" stroke-width="2"/>${button ? `<path d="M132 72v44" stroke="${dark}" stroke-width="7"/><path d="M130 72v44" stroke="${base}" stroke-width="3"/><g fill="#e4d9c1"><circle cx="132" cy="84" r="1.9"/><circle cx="132" cy="97" r="1.9"/><circle cx="132" cy="109" r="1.9"/></g>` : ""}${/graphic|butterfly|tie-dye/.test(title) ? `<g opacity=".55"><path d="M112 113q-16-14-17 4 4 19 33 27-3-26-16-31zm37 0q16-14 17 4-4 19-33 27 3-26 16-31z" fill="#b38369"/><path d="M130 113v34" stroke="#595b4f" stroke-width="3"/></g>` : ""}`;
  }
  // Each SVG is an independent image; a unique gradient avoids cross-card ID collisions.
  const id = `fabric-${++illustrationSequence}-${compact ? "small" : "large"}`;
  return `<svg viewBox="0 0 260 250" aria-hidden="true" focusable="false"><defs><linearGradient id="${id}" x1="0" x2="1" y2="1"><stop stop-color="${base}"/><stop offset="1" stop-color="${dark}"/></linearGradient></defs><ellipse cx="132" cy="224" rx="68" ry="6" fill="#454a37" opacity=".07"/><g transform="rotate(${item.category === "shoes" ? "0" : item.category === "bottoms" ? "5" : "-5"} 130 130)">${art.replaceAll("url(#fabric)", `url(#${id})`)}</g></svg>`;
}
