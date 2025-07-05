import { ImageResponse } from "next/og"

// Image metadata
export const size = {
  width: 64,
  height: 64,
}
export const contentType = "image/png"

// Image generation
export default function Icon() {
  return new ImageResponse(
    <div
      style={{
        background: "linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: "12px",
      }}
    >
      {/* Dumbbell Icon */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Left weight */}
        <div
          style={{
            width: "12px",
            height: "20px",
            background: "#ffffff",
            borderRadius: "2px",
          }}
        />
        {/* Left connector */}
        <div
          style={{
            width: "4px",
            height: "8px",
            background: "#ffffff",
            borderRadius: "1px",
          }}
        />
        {/* Handle */}
        <div
          style={{
            width: "16px",
            height: "4px",
            background: "#ffffff",
            borderRadius: "2px",
          }}
        />
        {/* Right connector */}
        <div
          style={{
            width: "4px",
            height: "8px",
            background: "#ffffff",
            borderRadius: "1px",
          }}
        />
        {/* Right weight */}
        <div
          style={{
            width: "12px",
            height: "20px",
            background: "#ffffff",
            borderRadius: "2px",
          }}
        />
      </div>
    </div>,
    {
      ...size,
    },
  )
}
