import React from "react";
import { Composition } from "remotion";
import { SubtitlesOverlay, SubtitlesOverlayProps } from "./SubtitlesOverlay";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CaptionsOverlay"
      component={SubtitlesOverlay}
      durationInFrames={300}
      fps={30}
      width={768}
      height={1344}
      defaultProps={{
        subtitles: [
          {
            start: 0.5,
            end: 4.5,
            text: "Welcome to Agnes Video Generator with Remotion Subtitles",
          },
        ],
        style: {
          fontSize: 48,
          highlightColor: "#FBBF24",
          textColor: "#FFFFFF",
        },
      }}
    />
  );
};
