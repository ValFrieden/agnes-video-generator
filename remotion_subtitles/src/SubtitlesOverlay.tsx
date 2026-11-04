import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

export interface WordCue {
  word: string;
  start: number; // in seconds
  end: number;   // in seconds
}

export interface SubtitleItem {
  id?: number;
  start: number; // in seconds
  end: number;   // in seconds
  text: string;
  words?: WordCue[];
}

export interface SubtitleStyleOptions {
  fontSize?: number;
  textColor?: string;
  highlightColor?: string;
  backgroundColor?: string;
  fontFamily?: string;
  positionY?: number | string; // e.g. "82%" or 800
  strokeColor?: string;
  strokeWidth?: number;
}

export interface SubtitlesOverlayProps {
  subtitles: SubtitleItem[];
  style?: SubtitleStyleOptions;
}

export const SubtitlesOverlay: React.FC<SubtitlesOverlayProps> = ({
  subtitles = [],
  style = {},
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const currentTime = frame / fps;

  // Find currently active subtitle
  const activeSub = subtitles.find(
    (sub) => currentTime >= sub.start && currentTime <= sub.end
  );

  if (!activeSub) {
    return null;
  }

  // Animation spring on subtitle entrance
  const subStartFrame = Math.floor(activeSub.start * fps);
  const enterProgress = spring({
    frame: frame - subStartFrame,
    fps,
    config: {
      damping: 14,
      stiffness: 120,
    },
  });

  const opacity = interpolate(enterProgress, [0, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(enterProgress, [0, 1], [15, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const fontSize = style.fontSize || Math.round(width * 0.045);
  const textColor = style.textColor || "#FFFFFF";
  const highlightColor = style.highlightColor || "#FBBF24"; // vibrant yellow/amber
  const strokeColor = style.strokeColor || "rgba(0, 0, 0, 0.85)";
  const strokeWidth = style.strokeWidth || 4;
  const fontFamily = style.fontFamily || "'Inter', 'Helvetica Neue', Arial, sans-serif";

  // Position calculation
  let topPosition: string | number = "82%";
  if (style.positionY !== undefined) {
    if (typeof style.positionY === "string") {
      topPosition = style.positionY;
    } else if (typeof style.positionY === "number") {
      topPosition = `${style.positionY}px`;
    }
  }

  // Render words if word cues exist, else fallback to text
  const words = activeSub.words && activeSub.words.length > 0
    ? activeSub.words
    : activeSub.text.split(" ").map((w, idx, arr) => {
        const segDuration = activeSub.end - activeSub.start;
        const wStart = activeSub.start + (idx / arr.length) * segDuration;
        const wEnd = activeSub.start + ((idx + 1) / arr.length) * segDuration;
        return { word: w, start: wStart, end: wEnd };
      });

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: topPosition,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none",
        transform: `translateY(${translateY}px)`,
        opacity,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          maxWidth: "88%",
          gap: "8px 12px",
          padding: "10px 20px",
          borderRadius: "14px",
          background: style.backgroundColor || "rgba(0, 0, 0, 0.45)",
          backdropFilter: "blur(4px)",
        }}
      >
        {words.map((item, index) => {
          const isWordActive = currentTime >= item.start && currentTime < item.end;
          return (
            <span
              key={`${item.word}-${index}`}
              style={{
                fontFamily,
                fontSize: `${fontSize}px`,
                fontWeight: isWordActive ? 800 : 700,
                color: isWordActive ? highlightColor : textColor,
                textShadow: `${strokeWidth}px ${strokeWidth}px 0px ${strokeColor}, -${strokeWidth}px -${strokeWidth}px 0px ${strokeColor}, ${strokeWidth}px -${strokeWidth}px 0px ${strokeColor}, -${strokeWidth}px ${strokeWidth}px 0px ${strokeColor}`,
                transform: isWordActive ? "scale(1.14)" : "scale(1.0)",
                transition: "all 0.08s ease-out",
                display: "inline-block",
                letterSpacing: "0.5px",
              }}
            >
              {item.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
