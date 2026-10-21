import postcss, { type Plugin } from "postcss";

/**
 * Makes Tailwind v4 output work inside a Shadow DOM root:
 *
 * 1. `:root` never matches inside a shadow tree -> rewrite it to `:host`
 *    (theme variables then live on the widget's host element).
 * 2. Browsers ignore `@property` inside shadow roots, so the `--tw-*` initial
 *    values that shadows/rings/transforms rely on would be missing -> emit them
 *    as plain declarations in the lowest-priority `properties` layer.
 * 3. `rem` is relative to the HOST page's <html> font-size, which we do not
 *    control -> convert to px (16px base) so host CSS cannot rescale the widget.
 */
export function shadowDomCss(): Plugin {
  return {
    postcssPlugin: "cursora-shadow-dom-css",
    OnceExit(root) {
      const fallbacks: postcss.Declaration[] = [];
      root.walkAtRules("property", (atRule) => {
        atRule.walkDecls("initial-value", (decl) => {
          // Keep `source`: Vite warns ("did not pass the `from` option") about decls without one.
          fallbacks.push(
            postcss.decl({ prop: atRule.params.trim(), value: decl.value, source: decl.source }),
          );
        });
      });

      root.walkRules((rule) => {
        if (!rule.selector.includes(":root")) return;
        rule.selectors = [...new Set(rule.selectors.map((s) => s.replace(/:root\b/g, ":host")))];
      });

      root.walkDecls((decl) => {
        decl.value = decl.value.replace(
          /(-?\d*\.?\d+)rem\b/g,
          (_, n: string) => `${Number.parseFloat(n) * 16}px`,
        );
      });

      if (fallbacks.length > 0) {
        const rule = postcss.rule({
          selectors: [":host", "*", "::before", "::after", "::backdrop"],
          source: root.source,
        });
        rule.append(fallbacks);
        root.prepend(
          postcss.atRule({ name: "layer", params: "properties", source: root.source }).append(rule),
        );
      }
    },
  };
}
