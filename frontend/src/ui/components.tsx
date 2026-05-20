import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type ButtonProps = PropsWithChildren<
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: "primary" | "secondary";
  }
>;

export function Button({ children, className = "", variant = "secondary", ...props }: ButtonProps) {
  return (
    <button className={`button button-${variant} ${className}`.trim()} type={props.type ?? "button"} {...props}>
      {children}
    </button>
  );
}

export function IconButton({ children, label }: PropsWithChildren<{ label: string }>) {
  return (
    <button className="icon-button" aria-label={label} title={label} type="button">
      {children}
    </button>
  );
}

export function StatusChip({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  return <span className={`status-chip status-${normalized}`}>{status.replaceAll("_", " ")}</span>;
}
