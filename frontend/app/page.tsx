export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16 flex flex-col items-center justify-center min-h-screen">

        {/* Main Title */}
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4">
            Chess <span className="text-blue-400">39</span>
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl">
            Random Armies, Infinite Strategy
          </p>
        </div>

        {/* Description Card */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-lg p-8 max-w-2xl mb-8 border border-slate-700">
          <h2 className="text-2xl font-semibold text-white mb-4">
            What is Chess 39?
          </h2>
          <p className="text-slate-300 leading-relaxed mb-4">
            Chess 39 is a unique chess variant where both players start with
            <span className="text-blue-400 font-semibold"> random armies worth exactly 39 points</span>.
          </p>
          <p className="text-slate-300 leading-relaxed mb-4">
            Instead of the traditional chess setup, each game begins with a different
            combination of pieces. You might have 4 queens, or 8 knights, or any
            combination that adds up to 39 points!
          </p>
          <div className="bg-slate-900/50 rounded p-4 mt-6">
            <p className="text-sm text-slate-400 mb-2">Point Values:</p>
            <div className="grid grid-cols-2 gap-2 text-slate-300">
              <div>♟ Pawn: <span className="text-blue-400">1 point</span></div>
              <div>♞ Knight: <span className="text-blue-400">3 points</span></div>
              <div>♝ Bishop: <span className="text-blue-400">3 points</span></div>
              <div>♜ Rook: <span className="text-blue-400">5 points</span></div>
              <div>♛ Queen: <span className="text-blue-400">9 points</span></div>
              <div>♚ King: <span className="text-blue-400">Always included</span></div>
            </div>
          </div>
        </div>

        {/* Call to Action Button */}
        <button className="bg-blue-500 hover:bg-blue-600 text-white font-semibold text-lg px-8 py-4 rounded-lg transition-colors duration-200 shadow-lg hover:shadow-xl">
          Play Now
        </button>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 max-w-4xl">
          <div className="text-center">
            <div className="text-4xl mb-2">🎲</div>
            <h3 className="text-white font-semibold mb-2">Random Armies</h3>
            <p className="text-slate-400 text-sm">
              Every game starts with a unique piece combination
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-2">🏆</div>
            <h3 className="text-white font-semibold mb-2">ELO Rankings</h3>
            <p className="text-slate-400 text-sm">
              Compete and climb the leaderboard
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-2">⚡</div>
            <h3 className="text-white font-semibold mb-2">Real-Time Play</h3>
            <p className="text-slate-400 text-sm">
              Instant move updates via WebSocket
            </p>
          </div>
        </div>

      </main>
    </div>
  );
}
