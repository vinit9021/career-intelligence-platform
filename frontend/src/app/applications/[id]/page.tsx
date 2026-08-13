import { ApplicationDetailsPage } from "@/components/applications/application-details-page";

interface ApplicationDetailsRouteProps {
  params: Promise<{
    id: string;
  }>;
}

export default async function Page({ params }: ApplicationDetailsRouteProps) {
  const { id } = await params;

  return <ApplicationDetailsPage applicationId={id} />;
}
