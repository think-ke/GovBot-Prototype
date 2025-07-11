import { AdminLayout } from "@/components/layout/admin-layout"
import { DashboardOverview } from "@/components/dashboard/dashboard-overview"

export default function AdminPage() {
  return (
    <AdminLayout>
      <DashboardOverview />
    </AdminLayout>
  )
}
