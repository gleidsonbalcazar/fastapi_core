import logging
import smtplib
from email.mime.text import MIMEText
from typing import Dict

import httpx

from app.core.config import settings
from app.domain.ports.email_port import EmailPort

logger = logging.getLogger(__name__)


class EmailAdapter(EmailPort):
    def __init__(self):
        self.host = settings.EMAIL_HOST
        self.port = settings.EMAIL_PORT
        self.username = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PASSWORD
        self.from_addr = settings.EMAIL_FROM_ADDR

    def send_email(self, to: str, subject: str, body: str):
        msg = MIMEText(body.encode("utf-8"), "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to

        try:
            with smtplib.SMTP_SSL(self.host, self.port) as server:
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, to, msg.as_string())
                print("Email enviado com sucesso!")
        except Exception as e:
            print(f"Erro ao enviar email: {e}")

    async def fetch_logo_and_theme(self, tenant: str) -> Dict[str, str]:
        try:
            async with httpx.AsyncClient() as client:
                logo_response = await client.get(
                    f"http://localhost:8000/api/v1/admin/tenant/logo/{tenant}"
                )
                logo_url = logo_response.text.strip()
                theme_response = await client.get(
                    f"http://localhost:8000/api/v1/admin/tenant/theme/{tenant}?response_type=object"
                )
                theme = theme_response.json()
            return {"logo_url": logo_url, **theme}
        except Exception as e:
            logger.error(
                f"Erro ao buscar logo e cores para o tenant {tenant}: {str(e)}"
            )
            return {}

    async def send_pin(self, to: str, pin: str, tenant: str, msg: str):
        subject = "Código de verificação"
        branding = await self.fetch_logo_and_theme(tenant)

        logo_svg = branding.get("logo_url")
        # cor1 = branding.get("--cor1", "#000000")
        cor2 = branding.get("--cor2", "#e4e4e4")
        cor_topo = branding.get("--cor1_light", "#ffffff")

        body = f"""
        <table style='width: 100%; max-width: 600px; font-family: Calibri, Verdana, Arial; margin: 0 auto; border-collapse: collapse;'>
          <thead>
              <tr>
                <th style='background-color: {cor_topo}; padding: 10px 0; text-align: center;'>
                  <div style='display: flex; justify-content: center; align-items: center; height: 60px;'>
                    <!-- Ajuste para redimensionar o SVG -->
                    <div style='width: 100px; height: auto;'>
                      <div style='width: 100%; height: 100%; display: inline-block; text-align: center;'>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 263.84207 145.56737" style="width: 100%; height: auto;">
                          {logo_svg}
                        </svg>
                      </div>
                    </div>
                  </div>
                </th>
              </tr>
          </thead>
          <tbody style='text-align: center; color: {cor2};'>
              <tr>
                  <td style='padding: 20px;'>
                      <h3 style='color: {cor2}; margin: 0;'>{msg}</h3>
                      <br />
                      <p style='font-size: 20px; color: {cor2};'>Seu PIN é: <strong>{pin}</strong></p>
                  </td>
              </tr>
          </tbody>
          <tfoot style='text-align: center;'>
              <tr>
                  <td style='font-size: 13px; padding: 20px; border-radius: 0 0 10px 10px; background-color: {cor2}; color: #fff;'>
                      <p style='text-align: left; margin: 0;'><strong>Dúvidas?</strong><br />
                      Esta é uma mensagem automática gerada pelo sistema. Por favor, não responder.<br /><br />
                      Não quer e-mails automáticos de ofertas e campanhas personalizadas? <a style="text-decoration:none; color:#fff" href='{{FRONT_URL}}/email_sender/unsubscribe/6026/{to}'>Cancele aqui</a></p>
                  </td>
              </tr>
          </tfoot>
        </table>
        """
        self.send_email(to, subject, body)

    async def send_email_recovery(self, to: str, tenant: str, msg: str):
        subject = "Recuperação de Senha Solicitada"
        branding = await self.fetch_logo_and_theme(tenant)

        logo_svg = branding.get("logo_url")
        # cor1 = branding.get("--cor1", "#000000")
        cor2 = branding.get("--cor2", "#e4e4e4")
        cor_topo = branding.get("--cor1_light", "#ffffff")

        body = f"""
        <table style='width: 100%; max-width: 600px; font-family: Calibri, Verdana, Arial; margin: 0 auto; border-collapse: collapse;'>
          <thead>
              <tr>
                <th style='background-color: {cor_topo}; padding: 10px 0; text-align: center;'>
                  <div style='display: flex; justify-content: center; align-items: center; height: 60px;'>
                    <!-- Ajuste para redimensionar o SVG -->
                    <div style='width: 100px; height: auto;'>
                      <div style='width: 100%; height: 100%; display: inline-block; text-align: center;'>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 263.84207 145.56737" style="width: 100%; height: auto;">
                          {logo_svg}
                        </svg>
                      </div>
                    </div>
                  </div>
                </th>
              </tr>
          </thead>
          <tbody style='text-align: center; color: {cor2};'>
              <tr>
                  <td style='padding: 20px;'>
                      <h3 style='color: {cor2}; margin: 0;'>{msg}</h3>
                      <br />
                  </td>
              </tr>
          </tbody>
          <tfoot style='text-align: center;'>
              <tr>
                  <td style='font-size: 13px; padding: 20px; border-radius: 0 0 10px 10px; background-color: {cor2}; color: #fff;'>
                      <p style='text-align: left; margin: 0;'><strong>Dúvidas?</strong><br />
                      Esta é uma mensagem automática gerada pelo sistema. Por favor, não responder.<br /><br />
                  </td>
              </tr>
          </tfoot>
        </table>
        """
        self.send_email(to, subject, body)
