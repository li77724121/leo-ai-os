import SwiftUI

struct HomeView: View {
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Logo区域
                    VStack(spacing: 12) {
                        Image(systemName: "paintpalette.fill")
                            .font(.system(size: 60))
                            .foregroundStyle(
                                LinearGradient(colors: [.orange, .pink], startPoint: .leading, endPoint: .trailing)
                            )
                        
                        Text("Leo Designer AI")
                            .font(.largeTitle)
                            .bold()
                        
                        Text("AI设计助手 · 生成海报/产品图/营销图")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.top, 40)
                    
                    // 功能卡片
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 16) {
                        FeatureCard(icon: "sparkles", title: "AI生成", desc: "文字描述生成图片", color: .orange)
                        FeatureCard(icon: "scissors", title: "AI抠图", desc: "一键去除背景", color: .blue)
                        FeatureCard(icon: "photo.on.rectangle", title: "换背景", desc: "智能背景替换", color: .green)
                        FeatureCard(icon: "square.on.square", title: "模板", desc: "商业海报模板", color: .purple)
                    }
                    .padding(.horizontal)
                    
                    // 开始按钮
                    NavigationLink(destination: CreateView()) {
                        HStack {
                            Image(systemName: "sparkles")
                            Text("开始AI创作")
                                .fontWeight(.semibold)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            LinearGradient(colors: [.orange, .pink], startPoint: .leading, endPoint: .trailing)
                        )
                        .foregroundColor(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                    }
                    .padding(.horizontal)
                    
                    Text("v1.0 MVP - 后续接入Hermes自动开发")
                        .font(.caption)
                        .foregroundColor(.secondary)
                        .padding(.bottom, 20)
                }
            }
            .navigationTitle("Leo Designer")
        }
    }
}

struct FeatureCard: View {
    let icon: String
    let title: String
    let desc: String
    let color: Color
    
    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: icon)
                .font(.title)
                .foregroundColor(color)
            
            Text(title)
                .font(.headline)
            
            Text(desc)
                .font(.caption)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(color.opacity(0.1))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(color.opacity(0.2), lineWidth: 1)
        )
    }
}

#Preview {
    HomeView()
}
