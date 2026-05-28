<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:otm="http://xmlns.oracle.com/apps/otm/synthetic"
  exclude-result-prefixes="otm">
  <xsl:output method="xml" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <Delivery>
      <DomainName><xsl:value-of select="//otm:DomainName"/></DomainName>
      <DeliveryId><xsl:value-of select="//otm:ShipmentGid"/></DeliveryId>
      <TransportMode><xsl:value-of select="//otm:TransportModeGid"/></TransportMode>
    </Delivery>
  </xsl:template>
</xsl:stylesheet>
