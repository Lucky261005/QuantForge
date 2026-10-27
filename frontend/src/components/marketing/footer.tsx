import Link from "next/link";

const links = [
  { href: "/#open", label: "How it works" },
  { href: "/#costs", label: "Charges" },
  { href: "/login", label: "Log in" },
  { href: "/register", label: "Create account" },
];

export function Footer() {
  return (
    <footer className="border-t border-border px-4 pb-8 pt-16 sm:px-6">
      <div className="grid gap-10 md:grid-cols-12">
        <p className="text-sm text-muted-foreground md:col-span-5">
          Research and education only. Not investment advice, and not connected to any broker. Charge rates are the
          ones modeled in the engine; check the current NSE and SEBI circulars before relying on them.
        </p>
        <ul className="flex flex-wrap gap-x-6 gap-y-3 md:col-span-6 md:col-start-7 md:justify-end">
          {links.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="inline-block py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-12">
        <p aria-hidden className="display select-none text-[clamp(2rem,4vw,3.5rem)] text-foreground">
          QuantForge<span className="text-primary">.</span>
        </p>
      </div>
      <p className="num mt-6 flex justify-between text-xs text-muted-foreground">
        <span>&copy; {new Date().getFullYear()} QuantForge</span>
        <span>Dalal Street hours, 09:15 to 15:30 IST</span>
      </p>
    </footer>
  );
}
