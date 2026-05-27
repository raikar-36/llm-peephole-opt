define i32 @chain_and_and_8_255(i32 %x) {
entry:
  %tmp = and i32 %x, 8
  %result = and i32 %tmp, 255
  ret i32 %result
}
