export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-16">
        <section className="w-full rounded-3xl border border-slate-800 bg-slate-900/70 p-10 shadow-2xl">
          <p className="mb-3 text-sm font-medium uppercase tracking-[0.2em] text-sky-300">
            FlyRank Internship · AI Decision Flow
          </p>

          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
            Build visual AI decisions as an executable graph.
          </h1>

          <p className="mt-6 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
            React Flow will provide the canvas. Inngest will execute each node as a
            durable workflow step. Decision nodes will return only YES or NO and
            follow the matching edge.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-3">
            {[
              ["Canvas", "Add, connect, move and edit workflow nodes."],
              ["Decision", "Route execution through YES and NO edges."],
              ["Execution", "Run the graph through durable Inngest steps."],
            ].map(([title, description]) => (
              <article
                key={title}
                className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5"
              >
                <h2 className="font-semibold text-white">{title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {description}
                </p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}