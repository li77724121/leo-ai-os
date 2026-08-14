import SwiftUI

struct GalleryView: View {
    @State private var artworks: [Artwork] = []
    
    var body: some View {
        NavigationStack {
            Group {
                if artworks.isEmpty {
                    ContentUnavailableView(
                        "还没有作品",
                        systemImage: "photo.on.rectangle",
                        description: Text("AI创作的作品将在这里显示")
                    )
                } else {
                    ScrollView {
                        LazyVGrid(columns: [
                            GridItem(.adaptive(minimum: 160), spacing: 12)
                        ], spacing: 12) {
                            ForEach(artworks) { artwork in
                                ImageCard(artwork: artwork)
                            }
                        }
                        .padding()
                    }
                }
            }
            .navigationTitle("我的作品")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("刷新", systemImage: "arrow.clockwise") {
                        loadArtworks()
                    }
                }
            }
            .onAppear {
                loadArtworks()
            }
        }
    }
    
    private func loadArtworks() {
        // TODO: 从本地SQLite加载
        // MVP阶段使用空列表
    }
}

#Preview {
    GalleryView()
}
