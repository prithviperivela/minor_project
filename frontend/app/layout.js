import "./globals.css";

export const metadata = {
  title: "SyteScan Prototype",
  description: "Interior site analysis and contractor discovery prototype",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
