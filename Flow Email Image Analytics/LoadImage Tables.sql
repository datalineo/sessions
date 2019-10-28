drop table if exists [dbo].[LoadImage]
drop table if exists [dbo].[LoadImageDetect]
drop table if exists [dbo].[LoadImageIdentify]
drop table if exists [dbo].[LoadImageIdentifyPerson]
drop table if exists [dbo].[LoadImageVision]


CREATE TABLE [dbo].[LoadImageVision](
	[FlowGUID] [uniqueidentifier] NOT NULL,
	ImageGUID [uniqueidentifier] NOT NULL,
	[ImageVision] [varchar](max) NULL )

CREATE TABLE [dbo].[LoadImage](
	[FlowGUID] [uniqueidentifier] NOT NULL,
	ImageGUID [uniqueidentifier] NOT NULL,
	[ImageFileName] [varchar](255) NULL,
	[ImageUri] [varchar](500) NULL,
	[ImageSize] [int] NULL,
	[FileModifiedDate] [datetime2](3) NULL,
	SenderEmail varchar(100) null ,
	[InsertedDate] [datetime2](3) NULL,
	[InsertedBy] [varchar](100) NULL
) ON [PRIMARY]
GO

ALTER TABLE [dbo].[LoadImage] ADD  DEFAULT (getdate()) FOR [InsertedDate]
GO

ALTER TABLE [dbo].[LoadImage] ADD  DEFAULT (suser_sname()) FOR [InsertedBy]
GO

CREATE TABLE [dbo].[LoadImageDetect](
	[FlowGUID] [uniqueidentifier] NOT NULL,
	ImageGUID [uniqueidentifier] NOT NULL,
	[DetectJSON] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

CREATE TABLE [dbo].[LoadImageIdentify](
	[FlowGUID] [uniqueidentifier] NOT NULL,
	ImageGUID [uniqueidentifier] NOT NULL,
	[IdentifyJSON] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO

CREATE TABLE [dbo].[LoadImageIdentifyPerson](
	[FlowGUID] [uniqueidentifier] NOT NULL,
	ImageGUID [uniqueidentifier] NOT NULL,
	[GetPersonJSON] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO


