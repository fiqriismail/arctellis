import Image from 'next/image'

interface AppIconProps {
  size?: number
  priority?: boolean
}

export function AppIcon({ size = 30, priority = false }: AppIconProps) {
  return (
    <Image
      src="/rtp-hub-icon.svg"
      alt="RTP Intelligence Hub"
      width={size}
      height={size}
      priority={priority}
    />
  )
}
