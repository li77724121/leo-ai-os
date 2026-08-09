import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Box, Orbit, Maximize2, RefreshCw, Download, Camera,
  Grid3x3, Layers, Cpu, Zap, Network, Move3d
} from 'lucide-react';
import { DigitalTwin3D } from '../components/DigitalTwin3D';
import { cn } from '../lib/utils';

export function Dashboard3D() {
  const [autoRotate, setAutoRotate] = useState(true);
  const [showGrid, setShowGrid] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showConnections, setShowConnections] = useState(true);

  return (
    <div className="h-full w-full relative bg-surface-950 overflow-hidden">
      {/* 3D 场景 */}
      <div className="absolute inset-0">
        <DigitalTwin3D 
          autoRotate={autoRotate}
          showGrid={showGrid}
          showLabels={showLabels}
          showConnections={showConnections}
        />
      </div>

      {/* 顶部工具栏 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="absolute top-4 left-1/2 -translate-x-1/2 glass-card px-4 py-2 flex items-center gap-2"
      >
        <span className="text-sm font-medium text-white mr-2">3D 数字孪生</span>
        <ToolButton active={autoRotate} onClick={() => setAutoRotate(!autoRotate)} title="自动旋转">
          <Orbit className="w-4 h-4" />
        </ToolButton>
        <ToolButton active={showGrid} onClick={() => setShowGrid(!showGrid)} title="网格">
          <Grid3x3 className="w-4 h-4" />
        </ToolButton>
        <ToolButton active={showLabels} onClick={() => setShowLabels(!showLabels)} title="标签">
          <Layers className="w-4 h-4" />
        </ToolButton>
        <ToolButton active={showConnections} onClick={() => setShowConnections(!showConnections)} title="连接线">
          <Network className="w-4 h-4" />
        </ToolButton>
        <div className="w-px h-6 bg-surface-700 mx-1" />
        <ToolButton onClick={() => {}} title="截图">
          <Download className="w-4 h-4" />
        </ToolButton>
        <ToolButton onClick={() => {}} title="重置视角">
          <RefreshCw className="w-4 h-4" />
        </ToolButton>
        <ToolButton onClick={() => {}} title="全屏">
          <Maximize2 className="w-4 h-4" />
        </ToolButton>
      </motion.div>

      {/* 底部提示 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="absolute bottom-4 left-1/2 -translate-x-1/2 text-xs text-surface-500 glass-card px-4 py-2"
      >
        拖动旋转 · 滚轮缩放 · 点击节点查看详情
      </motion.div>
    </div>
  );
}

function ToolButton({ active, onClick, title, children }: { active?: boolean; onClick: () => void; title: string; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={cn(
        'p-2 rounded-lg transition-colors',
        active ? 'bg-ai-500/20 text-ai-500' : 'text-surface-400 hover:bg-surface-800 hover:text-white'
      )}
    >
      {children}
    </button>
  );
}