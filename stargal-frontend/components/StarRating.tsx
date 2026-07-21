"use client"

interface Props {
  value: number
  max?: number
  size?: "sm" | "md" | "lg"
  readonly?: boolean
  onChange?: (value: number) => void
}

const sizeMap = {
  sm: "h-3.5 w-3.5",
  md: "h-5 w-5",
  lg: "h-6 w-6",
}

export default function StarRating({
  value,
  max = 10,
  size = "md",
  readonly = false,
  onChange,
}: Props) {
  const stars = 5
  // Convert 0-10 scale to 0-5 stars
  const normalized = (value / max) * stars

  const handleClick = (starIndex: number) => {
    if (readonly || !onChange) return
    // Each star = 2 points on 0-10 scale
    onChange((starIndex + 1) * 2)
  }

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: stars }, (_, i) => {
        const fill = Math.min(1, Math.max(0, normalized - i))
        const isFull = fill >= 0.9
        const isHalf = fill >= 0.3 && fill < 0.9

        return (
          <button
            key={i}
            type="button"
            disabled={readonly}
            onClick={() => handleClick(i)}
            className={`${readonly ? "cursor-default" : "cursor-pointer"} relative`}
          >
            <svg
              className={`${sizeMap[size]} ${isFull || isHalf ? "text-amber-400" : "text-zinc-700"}`}
              fill={isFull ? "currentColor" : "none"}
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
              />
            </svg>
            {isHalf && (
              <div className="absolute inset-0 overflow-hidden" style={{ width: "50%" }}>
                <svg
                  className={`${sizeMap[size]} text-amber-400`}
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
                  />
                </svg>
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}
