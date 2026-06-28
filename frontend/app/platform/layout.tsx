import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Platform Admin | ClinicTime",
  robots: "noindex",
};

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  return children;
}
