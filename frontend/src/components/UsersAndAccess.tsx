import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function UsersAndAccess() {
  const [ssoConfig, setSsoConfig] = useState<any>({ sso_type: 'none' });

  useEffect(() => {
    fetch('/api/sso').then(r => r.json()).then(setSsoConfig).catch(console.error);
  }, []);

  const saveSso = async () => {
    await fetch('/api/sso', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ssoConfig)
    });
    alert("SSO settings saved.");
  };

  return (
    <Card className="bg-black/40 backdrop-blur-md border-white/10 shadow-2xl">
      <CardHeader>
        <CardTitle>Users & Access</CardTitle>
        <CardDescription>Manage Local Users, RBAC, and SSO Integrations</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="local" className="w-full">
          <TabsList className="w-full justify-start border-b border-white/10 rounded-none bg-transparent h-auto p-0 mb-6">
            <TabsTrigger value="local" className="data-[state=active]:bg-white/5 data-[state=active]:border-b-2 data-[state=active]:border-white rounded-none px-4 py-3">Local Users</TabsTrigger>
            <TabsTrigger value="rbac" className="data-[state=active]:bg-white/5 data-[state=active]:border-b-2 data-[state=active]:border-white rounded-none px-4 py-3">RBAC Policies</TabsTrigger>
            <TabsTrigger value="sso" className="data-[state=active]:bg-white/5 data-[state=active]:border-b-2 data-[state=active]:border-white rounded-none px-4 py-3">SSO Configuration</TabsTrigger>
          </TabsList>

          <TabsContent value="local" className="space-y-4">
             <div className="text-zinc-400 text-sm">Local user management currently resides in standard Auth tab. (Placeholder for consolidation)</div>
          </TabsContent>

          <TabsContent value="rbac" className="space-y-4">
            <div className="text-zinc-400 text-sm">Role-Based Access Control Policies (Placeholder)</div>
          </TabsContent>

          <TabsContent value="sso" className="space-y-4">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">SSO Type</label>
                <select
                  value={ssoConfig.sso_type}
                  onChange={e => setSsoConfig({ ...ssoConfig, sso_type: e.target.value })}
                  className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white"
                >
                  <option value="none">Disabled</option>
                  <option value="oidc">OIDC (Free/Pro)</option>
                  <option value="saml">SAML (Studio)</option>
                </select>
              </div>

              {ssoConfig.sso_type !== 'none' && (
                <div className="space-y-4 p-4 border border-white/10 rounded bg-black/20">
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Client ID</label>
                    <input
                      type="text"
                      value={ssoConfig.client_id || ''}
                      onChange={e => setSsoConfig({...ssoConfig, client_id: e.target.value})}
                      className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Client Secret</label>
                    <input
                      type="password"
                      value={ssoConfig.client_secret || ''}
                      onChange={e => setSsoConfig({...ssoConfig, client_secret: e.target.value})}
                      className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white"
                    />
                  </div>
                  {ssoConfig.sso_type === 'saml' ? (
                    <div>
                      <label className="block text-sm font-medium text-zinc-300 mb-2">Metadata URL</label>
                      <input
                        type="url"
                        value={ssoConfig.metadata_url || ''}
                        onChange={e => setSsoConfig({...ssoConfig, metadata_url: e.target.value})}
                        className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white"
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="block text-sm font-medium text-zinc-300 mb-2">Issuer URL</label>
                      <input
                        type="url"
                        value={ssoConfig.issuer_url || ''}
                        onChange={e => setSsoConfig({...ssoConfig, issuer_url: e.target.value})}
                        className="w-full bg-zinc-950 border border-white/10 rounded p-2 text-white"
                      />
                    </div>
                  )}
                  <button onClick={saveSso} className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm font-medium">Save SSO Config</button>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
