export default function Footer() {
  return (
    <footer className="border-t border-zinc-800 bg-zinc-950">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
          <span className="text-lg font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            StarGal
          </span>
          <p className="text-xs text-zinc-500">
            Galgame 文化交流社区 &middot; 数据来源于 Bangumi &amp; VNDB
          </p>
        </div>
      </div>
    </footer>
  )
}
