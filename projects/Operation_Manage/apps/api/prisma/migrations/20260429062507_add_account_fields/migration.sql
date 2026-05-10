-- AlterTable
ALTER TABLE "accounts" ADD COLUMN     "account_type" VARCHAR(50),
ADD COLUMN     "common_devices" TEXT,
ADD COLUMN     "linked_phone" VARCHAR(20),
ADD COLUMN     "login_email" VARCHAR(100),
ADD COLUMN     "login_password" VARCHAR(255),
ADD COLUMN     "login_phone" VARCHAR(20),
ADD COLUMN     "registered_at" DATE,
ADD COLUMN     "remark" TEXT;
