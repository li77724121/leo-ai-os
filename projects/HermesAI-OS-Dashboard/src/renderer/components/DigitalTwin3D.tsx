// ============================================================
// 3D 数字孪生核心组件
// Leo AI Company Digital Twin - Three.js + React Three Fiber
// ============================================================

import React, { useRef, useState, useEffect, Suspense, lazy } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { 
  OrbitControls, 
  Html, 
  Stage, 
  Environment, 
  ContactShadows,
  Stars,
  Effects,
  Bloom,
  useGLTF,
  useTexture
} from '@react-three/drei';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';
import { useEventBus } from '../context/EventBusContext';
import { useConfig } from '../context/ConfigContext';

// ===== 自定义着色器材质 =====
const BrainMaterial = () => {
  const uniforms = {
    uTime: { value: 0 },
    uColor1: { value: new THREE.Color(0x06b6d4) }, // ai-500
    uColor2: { value: new THREE.Color(0x8b5cf6) }, // purple-500
    uColor3: { value: new THREE.Color(0xf59e0b) }, // amber-500
  };

  const material = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vNormal;
      varying vec3 vPosition;
      void main() {
        vUv = uv;
        vNormal = normalize(normalMatrix * normal);
        vPosition = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      uniform float uTime;
      uniform vec3 uColor1;
      uniform vec3 uColor2;
      uniform vec3 uColor3;
      varying vec2 vUv;
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      float noise(vec3 p) {
        return fract(sin(dot(p, vec3(12.9898, 78.233, 45.164))) * 43758.5453);
      }
      
      float fbm(vec3 p) {
        float value = 0.0;
        float amplitude = 0.5;
        for (int i = 0; i < 5; i++) {
          value += amplitude * noise(p);
          p *= 2.0;
          amplitude *= 0.5;
        }
        return value;
      }
      
      void main() {
        float n = fbm(vPosition * 2.0 + uTime * 0.3);
        float pulse = sin(uTime * 2.0 + vUv.x * 10.0) * 0.5 + 0.5;
        float edge = 1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0)));
        
        vec3 color = mix(uColor1, uColor2, n * 0.5 + 0.5);
        color = mix(color, uColor3, pulse * 0.3);
        color = mix(vec3(0.01), color, edge * 0.5 + n * 0.3);
        
        float alpha = edge * 0.6 + n * 0.4 + pulse * 0.2;
        
        gl_FragColor = vec4(color, alpha * 0.8);
      }
    `,
    transparent: true,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });

  useFrame((_, delta) => {
    uniforms.uTime.value += delta * 0.5;
  });

  return <meshGeometry />; // 占位，实际在组件中使用
};

// ===== 节点组件 =====
interface Node3DProps {
  position: [number, number, number];
  name: string;
  status: 'online' | 'offline' | 'warning';
  role: string;
  metrics?: { cpu: number; ram: number };
  showLabel?: boolean;
  onClick?: () => void;
}

const Node3D: React.FC<Node3DProps> = ({ position, name, status, role, metrics, showLabel = true, onClick }) => {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);
  const { state: eventState } = useEventBus();

  const statusColors = {
    online: 0x06b6d4,
    warning: 0xf59e0b,
    offline: 0xef4444,
  };

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.1;
      // 脉冲动画
      const scale = 1 + Math.sin(performance.now() * 0.002) * 0.05;
      groupRef.current.scale.setScalar(scale);
    }
  });

  const statusColor = statusColors[status];

  return (
    <group ref={groupRef} position={position} onClick={onClick} onPointerOver={() => setHovered(true)} onPointerOut={() => setHovered(false)}>
      {/* 外层发光环 */}
      <mesh>
        <torusGeometry args={[2.5, 0.08, 8, 32]} />
        <meshBasicMaterial 
          color={statusColor} 
          transparent 
          opacity={0.3}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* 内层脉冲环 */}
      <mesh>
        <torusGeometry args={[1.8, 0.05, 8, 32]} />
        <meshBasicMaterial 
          color={statusColor} 
          transparent 
          opacity={0.5}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* 核心球体 - 使用着色器 */}
      <mesh>
        <sphereGeometry args={[1.2, 32, 32]} />
        <meshPhysicalMaterial
          color={statusColor}
          metalness={0.2}
          roughness={0.3}
          transparent
          opacity={0.9}
          transmission={0.3}
          thickness={0.5}
          clearcoat={1}
          clearcoatRoughness={0.1}
        />
      </mesh>

      {/* 内核发光核心 */}
      <mesh>
        <sphereGeometry args={[0.6, 16, 16]} />
        <meshBasicMaterial 
          color={statusColor} 
          transparent 
          opacity={0.6}
          blending={THREE.AdditiveBlending}
        />
      </mesh>

      {/* 数据流粒子 */}
      <DataFlowParticles color={statusColor} count={50} radius={2} />

      {/* HTML 标签 */}
      {showLabel && (
      <Html position={[0, 3.5, 0]} transform={false} sprite>
        <div className={cn('pointer-events-none', 'transition-opacity duration-300')}>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-surface-950/95 backdrop-blur-xl border border-surface-700/50 rounded-xl p-3 min-w-[180px] text-center shadow-2xl"
            style={{ boxShadow: `0 0 30px ${statusColor}` }}
          >
            <div className="flex items-center justify-center gap-2 mb-2">
              <span 
                className="w-3 h-3 rounded-full animate-pulse"
                style={{ backgroundColor: `#${statusColor.toString(16).padStart(6, '0')}` }}
              />
              <span className="font-semibold text-white">{name}</span>
            </motion.div>
            <div className="text-xs text-surface-400 mb-1">{role}</div>
            <div className="flex justify-center gap-4 text-xs">
              <span className="text-ai-500">CPU: {Math.floor(Math.random() * 30 + 10)}%</span>
              <span className="text-purple-500">RAM: {Math.floor(Math.random() * 30 + 40)}%</span>
            </div>
          </motion.div>
        </div>
      </Html>
      )}
    </group>
  );
}

// 数据流粒子
const DataFlowParticles: React.FC<{ color: number; count: number; radius: number }> = ({ color, count, radius }) => {
  const pointsRef = useRef<THREE.Points>(null);
  const positions = new Float32Array(count * 3);
  const velocities = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const colors = new Float32Array(count * 3);

  // 初始化粒子
  for (let i = 0; i < count; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const r = radius * (0.5 + Math.random() * 0.5);
    
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = r * Math.cos(phi);
    
    velocities[i * 3] = (Math.random() - 0.5) * 0.02;
    velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.02;
    velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.02;
    
    sizes[i] = Math.random() * 0.1 + 0.05;
    
    const c = new THREE.Color(color);
    colors[i * 3] = c.r;
    colors[i * 3 + 1] = c.g;
    colors[i * 3 + 2] = c.b;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.1,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
  });

  useFrame((_, delta) => {
    if (pointsRef.current) {
      const positions = pointsRef.current.geometry.attributes.position.array;
      const velocities = pointsRef.current.userData.velocities;
      
      for (let i = 0; i < count; i++) {
        positions[i * 3] += velocities[i * 3];
        positions[i * 3 + 1] += velocities[i * 3 + 1];
        positions[i * 3 + 2] += velocities[i * 3 + 2];
        
        // 边界反弹
        const dist = Math.sqrt(
          positions[i * 3] ** 2 + 
          positions[i * 3 + 1] ** 2 + 
          positions[i * 3 + 2] ** 2
        );
        if (dist > radius * 1.5) {
          positions[i * 3] *= -0.5;
          positions[i * 3 + 1] *= -0.5;
          positions[i * 3 + 2] *= -0.5;
        }
      }
      pointsRef.current.geometry.attributes.position.needsUpdate = true;
      pointsRef.current.rotation.y += delta * 0.05;
    }
  });

  return (
    <points 
      ref={pointsRef} 
      geometry={geometry} 
      material={material}
      userData={{ velocities }}
    />
  );
}

// ===== 连接线组件 =====
interface ConnectionProps {
  start: [number, number, number];
  end: [number, number, number];
  active?: boolean;
  dataFlow?: number;
}

const Connection3D: React.FC<ConnectionProps> = ({ start, end, active, dataFlow = 0 }) => {
  const curveRef = useRef<THREE.CatmullRomCurve3>(null);
  const [progress, setProgress] = useState(0);

  useFrame((_, delta) => {
    if (active) {
      setProgress(p => (p + delta * 0.5 * (dataFlow + 0.5)) % 1);
    }
  });

  const midPoint = [
    (start[0] + end[0]) / 2,
    (start[1] + end[1]) / 2 + 3,
    (start[2] + end[2]) / 2,
  ];

  if (!curveRef.current) {
    curveRef.current = new THREE.CatmullRomCurve3([
      new THREE.Vector3(...start),
      new THREE.Vector3(...midPoint),
      new THREE.Vector3(...end),
    ]);
  }

  const points = curveRef.current.getPoints(50);
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  
  const material = new THREE.LineBasicMaterial({
    color: active ? 0x06b6d4 : 0x475569,
    transparent: true,
    opacity: active ? 0.8 : 0.3,
    linewidth: 2,
  });

  // 数据流动粒子
  const flowGeometry = new THREE.BufferGeometry();
  const flowPositions = new Float32Array(20 * 3);
  for (let i = 0; i < 20; i++) {
    const t = (progress + i * 0.05) % 1;
    const point = curveRef.current.getPoint(t);
    flowPositions[i * 3] = point.x;
    flowPositions[i * 3 + 1] = point.y;
    flowPositions[i * 3 + 2] = point.z;
  }
  const flowGeometry2 = new THREE.BufferGeometry();
  flowGeometry2.setAttribute('position', new THREE.BufferAttribute(flowPositions, 3));
  const flowMaterial = new THREE.PointsMaterial({
    color: 0x06b6d4,
    size: 0.15,
    transparent: true,
    opacity: 0.9,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
  });

  return (
    <group>
      <line geometry={geometry} material={material} />
      {active && (
        <points geometry={flowGeometry2} material={flowMaterial} />
      )}
    </group>
  );
}

// ===== 3D 公司地图主场景 =====
export function CompanyMap3D({ autoRotate = true, showGrid = true, showLabels = true, showConnections = true }: {
  autoRotate?: boolean;
  showGrid?: boolean;
  showLabels?: boolean;
  showConnections?: boolean;
}) {
  const { state: eventState } = useEventBus();
  const { state: configState } = useConfig();
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'overview' | 'detail'>('overview');

  // 自动旋转控制
  const controlsRef = useRef<any>(null);
  useFrame((_, delta) => {
    if (controlsRef.current && autoRotate) {
      controlsRef.current.rotateSpeed = 0.5;
    }
  });

  // 节点数据
  const nodes = useMemo(() => [
    {
      id: 'macbook',
      name: 'MacBook Pro M2',
      position: [-12, 2, 0] as [number, number, number],
      role: 'Hermes Master Brain',
      status: 'online' as const,
      metrics: { cpu: 12, ram: 45 },
    },
    {
      id: 'macmini',
      name: 'Mac mini M1',
      position: [0, 0, 0] as [number, number, number],
      role: 'CTO 研发中心',
      status: 'online' as const,
      metrics: { cpu: 35, ram: 68 },
    },
    {
      id: 'nas',
      name: '极空间 Z2S',
      position: [12, -2, 0] as [number, number, number],
      role: 'AI 运营中心',
      status: 'offline' as const,
      metrics: { cpu: 15, ram: 32 },
    },
    {
      id: 'openrouter',
      name: 'OpenRouter Cloud',
      position: [0, 10, 0] as [number, number, number],
      role: '全球 AI 专家库',
      status: 'online' as const,
      metrics: { cpu: 0, ram: 0 },
    },
  ], []);

  const connections = [
    { from: 'macbook', to: 'macmini', dataFlow: 0.8 },
    { from: 'macbook', to: 'nas', dataFlow: 0.3 },
    { from: 'macbook', to: 'openrouter', dataFlow: 0.9 },
    { from: 'macmini', to: 'nas', dataFlow: 0.6 },
  ];

  return (
    <div className="relative w-full h-full">
      <Canvas
        camera={{ position: [0, 5, 20], fov: 45 }}
        style={{ width: '100%', height: '100%' }}
        gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true }}
      >
        {/* 环境光 */}
        <ambientLight intensity={0.5} color="#ffffff" />
        <directionalLight position={[10, 15, 10]} intensity={1.5} color="#ffffff" castShadow />
        <directionalLight position={[-10, 10, -10]} intensity={0.5} color="#8b5cf6" />
        <pointLight position={[0, 5, 0]} intensity={1} color="#06b6d4" decay={1.5} distance={30} />
        <pointLight position={[0, -5, 0]} intensity={0.5} color="#8b5cf6" decay={1.5} distance={30} />

        {/* 星空背景 */}
        <Stars radius={100} depth={50} count={2000} saturation={0} factor={4} opacity={0.3} />

        {/* 地面 */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -5, 0]} receiveShadow>
          <planeGeometry args={[100, 100]} />
          <meshStandardMaterial 
            color="#020617" 
            metalness={0.1} 
            roughness={0.9}
            transparent
            opacity={0.3}
          />
        </mesh>

        {/* 网格地面线 */}
        {showGrid && <GridHelper args={[100, 20, '#1e293b', '#0f172a']} position={[0, -4.9, 0]} />}

        {/* 节点 */}
        {nodes.map((node) => (
          <Node3D
            key={node.id}
            position={node.position}
            name={node.name}
            status={node.status}
            role={node.role}
            metrics={node.metrics}
            showLabel={showLabels}
            onClick={() => setSelectedNode(node.id)}
          />
        ))}

        {/* 连接线 */}
        {showConnections && connections.map((conn, i) => {
          const fromNode = nodes.find(n => n.id === conn.from);
          const toNode = nodes.find(n => n.id === conn.to);
          return fromNode && toNode ? (
            <Connection3D
              key={i}
              start={fromNode.position}
              end={toNode.position}
              active={true}
              dataFlow={conn.dataFlow}
            />
          ) : null;
        })}

        {/* OpenRouter 云端节点特效 */}
        {showLabels && <CloudNode position={[0, 10, 0]} />}

        {/* OrbitControls */}
        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={0.05}
          autoRotate={autoRotate}
          autoRotateSpeed={0.5}
          minDistance={5}
          maxDistance={50}
        />

        {/* 选中节点详情面板 */}
        <Html position={[0, -8, 0]} transform={false} sprite>
          <SelectedNodePanel 
            node={nodes.find(n => n.id === selectedNode)} 
            onClose={() => setSelectedNode(null)}
          />
        </Html>
      </Canvas>

      {/* 控制面板 */}
      <div className="absolute bottom-4 left-4 right-4 md:left-4 md:right-auto md:w-64 md:bottom-4 md:top-4">
        <ControlPanel 
          viewMode={viewMode} 
          onViewModeChange={setViewMode}
          selectedNode={selectedNode}
          nodes={nodes}
        />
      </div>

      {/* 右侧状态面板 */}
      <div className="absolute top-4 right-4 md:right-4 md:top-4 md:w-72">
        <StatusPanel nodes={nodes} connections={connections} />
      </div>
    </div>
  );
}

// 云端节点特效
function CloudNode({ position }: { position: [number, number, number] }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.02;
      groupRef.current.position.y = position[1] + Math.sin(performance.now() * 0.001) * 0.5;
    }
  });

  return (
    <group ref={groupRef} position={position}>
      {/* 云层 */}
      {[0, 1, 2].map((i) => (
        <mesh key={i} position={[0, i * 0.5, 0]} scale={[3 - i * 0.5, 1, 3 - i * 0.5]}>
          <sphereGeometry args={[2.5, 16, 16]} />
          <meshPhysicalMaterial
            color="#06b6d4"
            transparent
            opacity={0.15 - i * 0.03}
            transmission={0.5}
            roughness={0.1}
            metalness={0}
            clearcoat={1}
          />
        </mesh>
      ))}
      
      {/* 光环 */}
      <mesh>
        <ringGeometry args={[4, 6, 32]} />
        <meshBasicMaterial 
          color="#06b6d4" 
          transparent 
          opacity={0.2}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* 数据流上升粒子 */}
      <DataFlowParticles color={0x06b6d4} count={30} radius={3} />
    </group>
  );
}

// 选中节点详情面板
function SelectedNodePanel({ node, onClose }: { node: any; onClose: () => void }) {
  if (!node) return null;

  const statusColors = {
    online: 'bg-green-500/20 text-green-500 border-green-500/30',
    warning: 'bg-amber-500/20 text-amber-500 border-amber-500/30',
    offline: 'bg-red-500/20 text-red-500 border-red-500/30',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className={`glass-card p-4 max-w-sm ${statusColors[node.status]}`}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-surface-800/50">
            <Bot className="w-5 h-5 text-ai-500" />
          </div>
          <div>
            <p className="font-semibold text-white">{node.name}</p>
            <p className="text-xs text-surface-400">{node.role}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1 rounded hover:bg-surface-800 text-surface-400">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${node.status === 'online' ? 'bg-green-500' : node.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
          <span className="text-sm text-white capitalize">{node.status}</span>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          <MetricMini label="CPU" value={`${Math.floor(Math.random() * 40 + 10)}%`} color="amber-500" />
          <MetricMini label="内存" value={`${Math.floor(Math.random() * 40 + 40)}%`} color="purple-500" />
          <MetricMini label="任务" value={Math.floor(Math.random() * 5 + 1)} color="ai-500" />
          <MetricMini label="模型" value="3" color="blue-500" />
        </div>

        <div className="pt-3 border-t border-surface-700/50">
          <button className="w-full btn-primary text-sm">
            查看详细监控
          </button>
        </div>
      </div>
    </motion.div>
  );
}

// 控制面板
function ControlPanel({ viewMode, onViewModeChange, selectedNode, nodes }: any) {
  const onlineCount = nodes.filter(n => n.status === 'online').length;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-ai-500" />
          Leo AI Company OS
        </h3>
        <span className="px-2 py-1 text-xs bg-ai-500/20 text-ai-500 rounded">V3.0</span>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <MetricMini label="在线节点" value={`${onlineCount}/${nodes.length}`} color="green-500" />
        <MetricMini label="总任务" value={Math.floor(Math.random() * 20 + 10)} color="ai-500" />
        <MetricMini label="Token成本" value={`$${(Math.random() * 2).toFixed(2)}`} color="amber-500" />
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" defaultChecked className="w-4 h-4 accent-ai-500" />
          <span className="text-sm text-surface-300">显示数据流动画</span>
        </label>
        <label className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" defaultChecked className="w-4 h-4 accent-ai-500" />
          <span className="text-sm text-surface-300">显示节点标签</span>
        </label>
        <label className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" className="w-4 h-4 accent-ai-500" />
          <span className="text-sm text-surface-300">显示连接线</span>
        </label>
      </div>

      <div className="pt-4 border-t border-surface-700/50 space-y-2">
        <button className="w-full btn-secondary text-sm justify-start gap-2">
          <RefreshCw className="w-4 h-4" />
          刷新所有节点
        </button>
        <button className="w-full btn-danger text-sm justify-start gap-2">
          <AlertTriangle className="w-4 h-4" />
          紧急停止所有任务
        </button>
      </div>
    </motion.div>
  );
}

// 状态面板
function StatusPanel({ nodes, connections }: any) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-card p-4 space-y-4"
    >
      <h3 className="font-semibold text-white flex items-center gap-2">
        <Activity className="w-5 h-5 text-ai-500" />
        实时状态
      </h3>

      <div className="space-y-3">
        {nodes.map((node: any) => (
          <div key={node.id} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface-800/50">
            <div className="flex items-center gap-3">
              <span className={`w-2.5 h-2.5 rounded-full ${node.status === 'online' ? 'bg-green-500' : node.status === 'warning' ? 'bg-amber-500' : 'bg-red-500'}`} />
              <div>
                <p className="font-medium text-white text-sm">{node.name}</p>
                <p className="text-xs text-surface-500">{node.role}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs font-mono text-ai-500">CPU: {Math.floor(Math.random() * 40 + 10)}%</p>
              <p className="text-xs font-mono text-purple-500">RAM: {Math.floor(Math.random() * 30 + 40)}%</p>
            </div>
          </div>
        ))}
      </div>

      <div className="pt-4 border-t border-surface-700/50 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-surface-400">活跃连接</span>
          <span className="font-mono text-green-500">{connections.length}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-surface-400">数据吞吐</span>
          <span className="font-mono text-ai-500">{Math.random() * 100 + 50} MB/s</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-surface-400">Token/小时</span>
          <span className="font-mono text-amber-500">$ {(Math.random() * 2).toFixed(2)}</span>
        </div>
      </div>
    </motion.div>
  );
}

// 导入需要的组件
import { Bot, Zap, AlertTriangle, RefreshCw, X, Activity, AlertCircle } from 'lucide-react';

// cn 工具函数
const cn = (...classes: (string | boolean | undefined | null)[]) => classes.filter(Boolean).join(' ');

// MetricMini 组件定义（避免循环依赖）
function MetricMini({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="text-center p-2 rounded-lg bg-surface-800/50">
      <p className="text-xs text-surface-500">{label}</p>
      <p className={`font-mono font-medium text-${color}`}>{value}</p>
    </div>
  );
}

// 导入 GridHelper
const GridHelper = ({ args, position }: { args: any[]; position: [number, number, number] }) => (
  <group position={position}>
    <gridHelper args={args} />
  </group>
);

// 暴露给外部的 Three.js 组件
export { Node3D, Connection3D, DataFlowParticles, CompanyMap3D };