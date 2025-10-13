import { AdminLayout } from "@/components/layout/admin-layout"
import { DocumentManager } from "@/components/documents/document-manager"

export default function DocumentsPage() {
  return (
    <AdminLayout>
      <DocumentManager />
    </AdminLayout>
  )
}
