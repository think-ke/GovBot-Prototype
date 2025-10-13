import { AdminLayout } from "@/components/layout/admin-layout"
import { WebsiteManager } from "@/components/websites/website-manager"

export default function WebsitesPage() {
  return (
    <AdminLayout>
      <WebsiteManager />
    </AdminLayout>
  )
}
