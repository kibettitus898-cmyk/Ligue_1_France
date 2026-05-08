import { Star } from "lucide-react";

const testimonials = [
  {
    name: "James Ochieng",
    role: "Nairobi, Kenya",
    content: "Went from losing 2k a week to making consistent profits. The EV badges alone changed how I think about betting entirely.",
    rating: 5,
  },
  {
    name: "Amina Hassan",
    role: "Mombasa, Kenya",
    content: "Finally a prediction site that doesn't just give tips. I can see WHY the model recommends each bet. Transparency is everything.",
    rating: 5,
  },
  {
    name: "David Kipchoge",
    role: "Nakuru, Kenya",
    content: "The M-Pesa integration is seamless. Subscribed for the monthly plan and the ROI has been incredible. Best betting investment I've made.",
    rating: 5,
  },
];

export function Testimonials() {
  return (
    <section className="relative py-24 bg-slate-950">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Trusted by Bettors Across East Africa
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            Join thousands of users who've transformed their betting strategy with data.
          </p>
        </div>
        
        <div className="grid gap-8 md:grid-cols-3">
          {testimonials.map((t) => (
            <div
              key={t.name}
              className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6"
            >
              <div className="flex gap-1 mb-4">
                {Array.from({ length: t.rating }).map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-accent-500 text-accent-500" />
                ))}
              </div>
              <p className="text-sm leading-relaxed text-slate-300 mb-6">
                "{t.content}"
              </p>
              <div>
                <p className="text-sm font-semibold text-white">{t.name}</p>
                <p className="text-xs text-slate-500">{t.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
