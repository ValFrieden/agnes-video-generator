#!/usr/bin/env node
/**
 * render.mjs — CLI для рендеринга анимированных субтитров через Remotion.
 *
 * Принимает JSON-файл с субтитрами, ширину, высоту и продолжительность,
 * и рендерит прозрачное видео с анимированными титрами (Apple ProRes / QuickTime Animation / VP9 Alpha).
 */

import path from "node:path";
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {
    propsPath: null,
    outputPath: null,
    width: 768,
    height: 1344,
    fps: 30,
    durationSec: 5.0,
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--props" && args[i + 1]) {
      params.propsPath = args[++i];
    } else if (args[i] === "--output" && args[i + 1]) {
      params.outputPath = args[++i];
    } else if (args[i] === "--width" && args[i + 1]) {
      params.width = parseInt(args[++i], 10);
    } else if (args[i] === "--height" && args[i + 1]) {
      params.height = parseInt(args[++i], 10);
    } else if (args[i] === "--fps" && args[i + 1]) {
      params.fps = parseInt(args[++i], 10);
    } else if (args[i] === "--duration" && args[i + 1]) {
      params.durationSec = parseFloat(args[++i]);
    }
  }
  return params;
}

async function main() {
  const params = parseArgs();

  if (!params.propsPath || !params.outputPath) {
    console.error("Usage: node render.mjs --props <props.json> --output <output.mov|webm> [--duration <sec>] [--width <w>] [--height <h>]");
    process.exit(1);
  }

  const propsRaw = fs.readFileSync(params.propsPath, "utf-8");
  const inputProps = JSON.parse(propsRaw);

  const durationInFrames = Math.max(Math.ceil(params.durationSec * params.fps), 1);

  console.log(`[RemotionSubtitles] Rendering ${durationInFrames} frames (${params.durationSec}s) at ${params.width}x${params.height} (${params.fps} fps)...`);

  try {
    const { bundle } = await import("@remotion/bundler");
    const { renderMedia, selectComposition } = await import("@remotion/renderer");

    const entryPoint = path.join(__dirname, "src", "index.ts");
    console.log(`[RemotionSubtitles] Bundling Remotion composition from ${entryPoint}...`);

    const bundleLocation = await bundle({
      entryPoint,
      webpackOverride: (config) => config,
    });

    console.log(`[RemotionSubtitles] Selecting composition...`);
    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "CaptionsOverlay",
      inputProps,
    });

    const isMov = params.outputPath.toLowerCase().endsWith(".mov");

    await renderMedia({
      composition: {
        ...composition,
        width: params.width,
        height: params.height,
        fps: params.fps,
        durationInFrames,
      },
      serveUrl: bundleLocation,
      codec: isMov ? "prores" : "vp9",
      proResProfile: isMov ? "4444" : undefined,
      pixelFormat: isMov ? "yuva444p10le" : "yuva420p",
      outputLocation: path.resolve(params.outputPath),
      inputProps,
      imageFormat: "png",
    });

    console.log(`[RemotionSubtitles] ✅ Render complete: ${params.outputPath}`);
  } catch (err) {
    console.error(`[RemotionSubtitles] ❌ Render failed:`, err);
    process.exit(1);
  }
}

main();
