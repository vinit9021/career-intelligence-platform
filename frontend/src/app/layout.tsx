import type { Metadata } from "next";
import type { ReactNode } from "react";

import { QueryProvider } from "@/providers/query-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Career Intelligence Platform",
    template: "%s | Career Intelligence Platform",
  },
  description:
    "An AI-powered operating system for job applications, resume intelligence, assessments, interviews, and career analytics.",
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
