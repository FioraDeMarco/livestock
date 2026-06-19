type CompanyLogoProps = {
  name: string;
  brandColor: string;
  size?: number;
  className?: string;
};

export default function CompanyLogo({
  name,
  brandColor,
  size = 56,
  className = "",
}: CompanyLogoProps) {
  const initial = name.charAt(0).toUpperCase();

  return (
    <div
      className={`flex items-center justify-center rounded-full font-bold text-white ${className}`}
      style={{
        width: size,
        height: size,
        backgroundColor: brandColor,
        fontSize: size * 0.42,
      }}
    >
      {initial}
    </div>
  );
}
