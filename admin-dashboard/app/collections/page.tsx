import { AdminLayout } from "@/components/layout/admin-layout"
import { CollectionManager } from "@/components/collections/collection-manager"

export default function CollectionsPage() {
  return (
    <AdminLayout>
      <CollectionManager />
    </AdminLayout>
  )
}
