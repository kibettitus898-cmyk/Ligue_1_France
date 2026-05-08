import { Hero } from "@/components/marketing/Hero";
import { Features } from "@/components/marketing/Features";
import { HowItWorks } from "@/components/marketing/HowItWorks";
import { Testimonials } from "@/components/marketing/Testimonials";
import { PricingCards } from "@/components/marketing/PricingCards";
import { CTA } from "@/components/marketing/CTA";
import { Footer } from "@/components/marketing/Footer";
import { MarketingNav } from "@/components/marketing/MarketingNav";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950">
      <MarketingNav />
      <main>
        <div className="pt-16">
          <Hero />
        </div>
        <Features />
        <HowItWorks />
        <Testimonials />
        <PricingCards />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
