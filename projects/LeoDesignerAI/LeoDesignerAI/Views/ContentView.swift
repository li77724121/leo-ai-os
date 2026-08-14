import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Image(systemName: "house")
                    Text("首页")
                }
            
            CreateView()
                .tabItem {
                    Image(systemName: "sparkles")
                    Text("AI创作")
                }
            
            GalleryView()
                .tabItem {
                    Image(systemName: "photo.on.rectangle")
                    Text("作品")
                }
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gearshape")
                    Text("设置")
                }
        }
        .accentColor(.orange)
    }
}

#Preview {
    ContentView()
}
