# --------------------------
# Modules needed
# --------------------------
#Install-Module -Name MicrosoftPowerBIMgmt -Force
#Install-Module -Name sqlserver -Force
#Install-Module -Name Azure -Force

# --------------------------
# Power BI Login
# --------------------------
#Login-PowerBI
cls

# ------------
# grab config details
# ------------
Write-Host("Setting configurables...")
$config = Get-Content -Path "C:\GIT\datalineo\config\config_flow_image_analytics.json" -Raw | ConvertFrom-Json
$datasetId = $config.powerbi.datasetid
$groupId = $config.powerbi.groupid
$tableName = $config.powerbi.tablename
$servername = $config.sqlserver.servername
$database = $config.sqlserver.database
$username = $config.sqlserver.username
$password = $config.sqlserver.password
$StorageAccountName = $config.storage.account
$StorageAccountKey = $config.storage.key
$ContainerName1 = $config.storage.container1
$ContainerName2 = $config.storage.container2

# ------------
# Clear Push Dataset
# ------------
Write-Host("Power BI Push dataset clearing...")
$URL = "https://api.powerbi.com/v1.0/myorg/groups/"+$groupId+"/datasets/"+$datasetId+"/tables/"+$tableName+"/rows"
$result = Invoke-PowerBIRestMethod -Url $URL -Method Delete

# ------------
# Empty SQL Tables
# ------------
Write-Host("SQL Tables truncating...")
$query = "truncate table LoadImage;truncate table LoadImageDetect;truncate table LoadImageIdentify;truncate table LoadImageIdentifyPerson;truncate table LoadImageVision;"
Invoke-Sqlcmd -ServerInstance $servername -Username $username -Password $password -Database $database -Query $query

# ------------
# Deleted attachment from Azure Blob
# ------------
Write-Host("Azure Blob emptying...")
$ctx = New-AzureStorageContext -StorageAccountName $StorageAccountName -StorageAccountKey $StorageAccountKey
Get-AzureStorageBlob -Container $ContainerName1 -Context $ctx | Remove-AzureStorageBlob 
Get-AzureStorageBlob -Container $ContainerName2 -Context $ctx | Remove-AzureStorageBlob 

# ------------
# Finito
# ------------
Write-Host("Done")
