type CompanyLogoProps = {
  name: string;
  ticker: string | null;
  brandColor: string;
  size?: number;
  className?: string;
};

export default function CompanyLogo({
  name,
  ticker,
  brandColor,
  size = 56,
  className = "",
}: CompanyLogoProps) {
  const initials = (ticker ?? name).slice(0, 2).toUpperCase();

  return (
    <div
      className={`flex items-center justify-center rounded-full font-bold text-white ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: brandColor,
        fontSize: size * 0.32,
      }}
    >
      {initials}
    </div>
  );
}
