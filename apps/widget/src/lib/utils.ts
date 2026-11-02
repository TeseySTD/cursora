// `unknown` because JSX `className` types differ per renderer (Preact adds signals); only strings count.
type ClassValue = unknown;

/**
 * Joins class names, skipping falsy values. Unlike shadcn's usual `clsx` + `tailwind-merge`, it does
 * not resolve conflicting Tailwind utilities (the bundle size matters in an embedded widget), so a
 * `className` override must not repeat a utility the component already sets: add a variant prop
 * instead (see `IconBadge`'s `tone`).
 */
export function cn(...inputs: ClassValue[]): string {
  const classes: string[] = [];
  for (const input of inputs) {
    if (Array.isArray(input)) {
      const nested = cn(...input);
      if (nested) classes.push(nested);
    } else if (typeof input === "string" && input) {
      classes.push(input);
    }
  }
  return classes.join(" ");
}
