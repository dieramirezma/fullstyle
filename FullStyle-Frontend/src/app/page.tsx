import Footer from '@/components/footer'
import NavBar from '@/components/nav-bar'
import BlogSection from '@/components/blog-section'
import HeroSection from '@/components/hero-section'
import ContactSection from '@/components/contact-section'
import InstanceInfo from '@/components/instance-info'

export default function Home() {
  return (
    <>
      <NavBar />
      <main className="flex flex-col gap-20 px-10 md:px-28">
        <HeroSection />
        <BlogSection />
        <ContactSection />
      </main>
      <Footer />
      <InstanceInfo />
    </>
  )
}
