/** Join class names, dropping falsy values (minimal cn helper). */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}
