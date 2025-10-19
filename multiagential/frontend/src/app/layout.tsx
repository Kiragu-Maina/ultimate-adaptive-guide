import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AlkenaCode School - Adaptive Learning Platform",
  description: "An adaptive learning mentor platform that provides personalized quizzes, content, and feedback to enhance your learning experience.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} antialiased`}
        suppressHydrationWarning={true}
      >
        {children}
        <div id="chat-agent-root">
          {/* Chat agent will be rendered here */}
        </div>
      </body>
    </html>
  );
}
