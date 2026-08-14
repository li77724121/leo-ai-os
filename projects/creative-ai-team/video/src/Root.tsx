import { Composition } from "remotion";
import { CreativeTeamVideo } from "./CreativeTeamVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="creative-team-video"
      component={CreativeTeamVideo}
      durationInFrames={180}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={{
        title: "AI 创意团队",
      }}
    />
  );
};
