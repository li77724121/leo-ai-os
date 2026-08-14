import SwiftUI

struct ImageCard: View {
    let artwork: Artwork
    
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let url = artwork.imageURL, let imageURL = URL(string: url) {
                AsyncImage(url: imageURL) { phase in
                    switch phase {
                    case .success(let img):
                        img
                            .resizable()
                            .scaledToFill()
                    case .failure:
                        Image(systemName: "photo")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                    case .empty:
                        ProgressView()
                    @unknown default:
                        EmptyView()
                    }
                }
                .frame(height: 160)
                .clipped()
            }
            
            Text(artwork.prompt)
                .font(.caption)
                .lineLimit(2)
                .padding(.horizontal, 8)
            
            Text(artwork.date, style: .date)
                .font(.caption2)
                .foregroundColor(.secondary)
                .padding(.horizontal, 8)
                .padding(.bottom, 8)
        }
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(Color(.systemGray5), lineWidth: 1)
        )
    }
}

#Preview {
    ImageCard(artwork: Artwork(id: UUID(), prompt: "测试图片", imageURL: nil, date: Date()))
        .frame(width: 180)
}
