import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from "remotion";

// Color palette
const COLORS = {
  bg: "#0a0a12",
  purple: "#a78bfa",
  pink: "#f472b6",
  cyan: "#22d3ee",
  green: "#34d399",
  text: "rgba(255,255,255,0.85)",
  dim: "rgba(255,255,255,0.4)",
  darkBorder: "rgba(255,255,255,0.06)",
};

const AGENTS = [
  { emoji: "🎨", name: "图像生成", tool: "ComfyUI · FLUX", color: COLORS.purple },
  { emoji: "🎬", name: "视频制作", tool: "Remotion · React", color: COLORS.pink },
  { emoji: "🎵", name: "音乐创作", tool: "Suno · Songwriting", color: COLORS.cyan },
  { emoji: "✍️", name: "内容润色", tool: "Humanizer · Voice", color: COLORS.green },
];

function GridBackground({ frame }: { frame: number }) {
  const opacity = interpolate(frame, [0, 30], [0, 0.05], {
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        opacity,
        backgroundImage: `
          linear-gradient(rgba(99,102,241,0.08) 1px, transparent 1px),
          linear-gradient(90deg, rgba(99,102,241,0.08) 1px, transparent 1px)
        `,
        backgroundSize: "60px 60px",
      }}
    />
  );
}

function AnimatedOrb({
  frame,
  size,
  color,
  x,
  y,
  delay,
}: {
  frame: number;
  size: number;
  color: string;
  x: number;
  y: number;
  delay: number;
}) {
  const progress = interpolate(frame - delay, [0, 90], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(progress, [0, 0.3, 1], [0, 0.25, 0.15]);
  const offsetY = interpolate(progress, [0, 1], [40, 0]);
  return (
    <div
      style={{
        position: "absolute",
        width: size,
        height: size,
        borderRadius: "50%",
        background: color,
        filter: "blur(100px)",
        opacity,
        left: x,
        top: y + offsetY,
        transform: `translate(-50%, -50%)`,
      }}
    />
  );
}

export const CreativeTeamVideo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Title animation
  const titleOpacity = interpolate(frame, [0, 25, 35], [0, 1, 1], {
    extrapolateRight: "clamp",
  });
  const titleScale = spring({
    frame: frame,
    fps,
    config: { damping: 12, mass: 0.5 },
  });

  // Subtitle animation
  const subOpacity = interpolate(frame, [25, 40], [0, 1], {
    extrapolateRight: "clamp",
  });

  // "Activating" text
  const activatingOpacity = interpolate(frame, [40, 55, 100], [0, 1, 1], {
    extrapolateRight: "clamp",
  });
  const loadingProgress = interpolate(frame, [55, 100], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Agents stagger
  const showAgents = frame >= 110;

  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg, overflow: "hidden" }}>
      <GridBackground frame={frame} />

      <AnimatedOrb
        frame={frame}
        size={400}
        color={COLORS.purple}
        x={15}
        y={30}
        delay={0}
      />
      <AnimatedOrb
        frame={frame}
        size={300}
        color={COLORS.pink}
        x={85}
        y={70}
        delay={15}
      />
      <AnimatedOrb
        frame={frame}
        size={250}
        color={COLORS.cyan}
        x={50}
        y={50}
        delay={30}
      />

      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: "20%",
          width: "100%",
          textAlign: "center",
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 800,
            lineHeight: 1,
            background: "linear-gradient(135deg, #a78bfa, #f472b6, #22d3ee)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            letterSpacing: -2,
            filter: "drop-shadow(0 0 30px rgba(167,139,250,0.3))",
          }}
        >
          AI 创意团队
        </div>
        <div
          style={{
            marginTop: 16,
            fontSize: 18,
            color: COLORS.dim,
            letterSpacing: 6,
            opacity: subOpacity,
            textTransform: "uppercase",
          }}
        >
          Creative AI · 4 Minds · One Vision
        </div>
      </div>

      {/* Loading / Activating */}
      <Sequence from={40}>
        <div
          style={{
            position: "absolute",
            top: "42%",
            width: "100%",
            textAlign: "center",
            opacity: activatingOpacity,
          }}
        >
          <div
            style={{
              fontSize: 16,
              color: COLORS.dim,
              letterSpacing: 4,
              marginBottom: 16,
              textTransform: "uppercase",
            }}
          >
            正在激活创意AI...
          </div>
          <div
            style={{
              width: "60%",
              height: 3,
              background: COLORS.darkBorder,
              borderRadius: 2,
              margin: "0 auto",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${loadingProgress * 100}%`,
                background: "linear-gradient(90deg, #a78bfa, #f472b6, #22d3ee)",
                borderRadius: 2,
              }}
            />
          </div>
        </div>
      </Sequence>

      {/* Four AI Agents */}
      {showAgents && (
        <div
          style={{
            position: "absolute",
            bottom: "18%",
            width: "100%",
            display: "flex",
            justifyContent: "center",
            gap: 40,
            padding: "0 30px",
          }}
        >
          {AGENTS.map((agent, i) => {
            const delay = 110 + i * 8;
            const scale = spring({
              frame: frame - delay,
              fps,
              config: { damping: 14, mass: 0.4 },
            });
            const opacity = interpolate(frame - delay, [0, 12], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });

            return (
              <div
                key={agent.name}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 10,
                  opacity,
                  transform: `scale(${scale})`,
                }}
              >
                <div
                  style={{
                    width: 76,
                    height: 76,
                    borderRadius: 20,
                    background: `linear-gradient(135deg, ${agent.color}, ${agent.color}88)`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 32,
                    boxShadow: `0 0 30px ${agent.color}33`,
                  }}
                >
                  {agent.emoji}
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: COLORS.text,
                    fontWeight: 600,
                    letterSpacing: 1,
                    textTransform: "uppercase",
                  }}
                >
                  {agent.name}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: COLORS.dim,
                    letterSpacing: 0.5,
                  }}
                >
                  {agent.tool}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom line */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          width: "60%",
          left: "20%",
          height: 1,
          background: `linear-gradient(90deg, transparent, ${COLORS.purple}44, ${COLORS.cyan}44, transparent)`,
          opacity: interpolate(frame, [140, 160], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />
    </AbsoluteFill>
  );
};
